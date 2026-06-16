import json
import requests
import os
import re
import hashlib
from datetime import datetime

CATEGORY_KEYWORDS = {
    '电子产品': ['手机', '电脑', '平板', '耳机', '相机', '键盘', '鼠标', '显示器', '笔记本', 'iphone', 'ipad', 'macbook', '数码', '电子'],
    '图书': ['书', '教材', '小说', '杂志', 'book'],
    '服装': ['衣服', '裤子', '鞋子', '外套', '裙子', 't恤', '衬衫', 'clothes', 'shoes'],
    '家具': ['桌子', '椅子', '床', '柜子', '沙发', '书架', 'desk', 'chair'],
    '运动': ['篮球', '足球', '羽毛球', '跑步', '健身', '运动', 'sports'],
    '乐器': ['吉他', '钢琴', '小提琴', 'guitar', 'piano'],
    '娱乐': ['游戏', 'switch', 'ps5', 'xbox', 'game', 'steam', '虚拟', '账号', '点卡', '皮肤', '会员', '充值', '代练', '陪玩', '直播', '视频', '影视', '音乐', '专辑', '演唱会', '桌游', '剧本杀', '密室', '棋牌', '麻将', '扑克','等级', '段位', '无畏契约', 'valorant', 'csgo', 'cs2', '原神', '王者荣耀', '英雄联盟', 'lol', 'apex', '永劫无间'],
    '化妆品': ['口红', '粉底', '面膜', '护肤', 'cosmetic'],
    '电脑硬件': ['显卡', 'cpu', '内存', '硬盘', '主板', '电源', '机箱', '散热器', 'rtx', 'gtx', 'amd', 'intel', 'nvidia', 'geforce'],
    '外设': ['键盘', '鼠标', '耳机', '音箱', '麦克风', '手柄', '外设'],
}


class TextClassifier:
    SELL_KEYWORDS = ['出售', '卖', '转让', 'sell', '闲置', '二手', '全新', '低价']
    BUY_KEYWORDS = ['求购', '买', '需要', 'buy', 'want', '收购', '想要', '急求']

    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or os.environ.get('QWEN_API_KEY', '')
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def _determine_category(self, title, description):
        """根据关键词列表确定商品大类，无匹配返回'其他'"""
        text = f'{title} {description}'.lower()
        best_category = None
        best_score = -1

        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score >= best_score:
                best_score = score
                best_category = category

        return best_category if best_score > 0 else '其他'

    def generate_tags_with_qwen(self, title, description):
        category = self._determine_category(title, description)

        if not self.api_key:
            result = self.generate_tags_by_keywords(title, description)
            tags = result['tags']
            if not tags or tags[0] != category:
                tags = [category] + [t for t in tags if t != category]
            return {
                'tags': tags[:8],
                'source': 'keyword'
            }

        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            data = {
                'model': 'qwen3.7-plus',
                'messages': [
                    {
                        'role': 'system',
                        'content': f'商品已确定类别为"{category}"。请根据商品信息生成3-5个除了类别以外的标签（如品牌、型号、成色、具体类型等）。禁止输出类别标签和"二手""闲置"等通用词。只返回JSON数组。'
                    },
                    {
                        'role': 'user',
                        'content': f'标题：{title}\n描述：{description}'
                    }
                ],
                'temperature': 0.3,
                'max_tokens': 200
            }

            response = requests.post(url, json=data, headers=headers, timeout=60)
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content'].strip()
                tags = json.loads(content)
                if isinstance(tags, list):
                    tags = [t for t in tags if t != category]
                    tags = [category] + tags
                    if len(tags) >= 2:
                        return {
                            'tags': tags[:8],
                            'source': 'qwen'
                        }

        except Exception as e:
            print(f'Qwen tag generation error: {e}')

        keyword_result = self.generate_tags_by_keywords(title, description)
        tags = keyword_result['tags']
        if not tags or tags[0] != category:
            tags = [category] + [t for t in tags if t != category]
        return {
            'tags': tags[:8],
            'source': 'keyword'
        }

    def estimate_price_with_qwen(self, title, description, condition):
        """使用Qwen模型估算二手商品价格"""
        if not self.api_key:
            return {'min_price': 0, 'max_price': 0, 'source': 'fallback'}

        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            data = {
                'model': 'qwen3.7-plus',
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是二手价格估算专家。根据商品信息估算价格，返回JSON：{"min_price":数字,"max_price":数字}。只返回JSON。'
                    },
                    {
                        'role': 'user',
                        'content': f'标题：{title}\n描述：{description}\n成色：{condition}'
                    }
                ],
                'temperature': 0.2,
                'max_tokens': 100
            }

            response = requests.post(url, json=data, headers=headers, timeout=60)
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content'].strip()
                parsed = json.loads(content)
                return {
                    'min_price': parsed.get('min_price', 0),
                    'max_price': parsed.get('max_price', 0),
                    'source': 'qwen'
                }

        except Exception as e:
            print(f'Qwen price estimation error: {e}')

        return {'min_price': 0, 'max_price': 0, 'source': 'error'}

    def generate_copywriting_with_qwen(self, title, description, condition=''):
        """使用Qwen模型生成高转化率的闲鱼/小红书风格文案"""
        if not self.api_key:
            return {'copywriting': '', 'source': 'fallback'}

        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            product_info = f"标题：{title}\n描述：{description}"
            if condition:
                product_info += f"\n成色：{condition}"

            data = {
                'model': 'qwen3.7-plus',
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是闲鱼文案写手。根据商品信息写80-150字的活泼文案，用2-3个emoji，突出性价比，结尾引导互动。只返回文案。'
                    },
                    {
                        'role': 'user',
                        'content': product_info
                    }
                ],
                'temperature': 0.8,
                'max_tokens': 500
            }

            response = requests.post(url, json=data, headers=headers, timeout=120)
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content'].strip()
                return {
                    'copywriting': content,
                    'source': 'qwen'
                }

        except Exception as e:
            print(f'Qwen copywriting generation error: {e}')

        return {'copywriting': '', 'source': 'error'}

    def generate_tags_by_keywords(self, title, description):
        text = f'{title} {description}'.lower()
        tags = []

        category = self._determine_category(title, description)
        tags.append(category)

        condition_keywords = {
            '全新未拆封': ['全新未拆封', '未拆封', '全新'],
            '几乎全新': ['几乎全新', '九成新', '99新', '几乎没使用'],
            '轻微使用痕迹': ['轻微使用', '轻微磨损', '细微使用', '细微磨损', '小瑕疵'],
            '中度使用痕迹': ['中度使用', '中度磨损', '明显使用', '明显磨损'],
            '严重使用痕迹': ['严重使用', '严重磨损', '大瑕疵', '破损'],
        }

        for condition, keywords in condition_keywords.items():
            if any(kw in text for kw in keywords):
                tags.append(condition)
                break

        brand_keywords = ['苹果', '华为', '小米', '三星', '索尼', 'nike', 'adidas', 'apple', 'huawei', 'nvidia', 'amd', 'intel', '华硕', '微星', '技嘉', '七彩虹', '影驰']
        for brand in brand_keywords:
            if brand in text:
                tags.append(brand)

        model_patterns = [
            r'(rtx\s*\d{4})', r'(gtx\s*\d{4})', r'(iphone\s*\d+)', r'(macbook\s*\w+)',
            r'(ipad\s*\w+)', r'(airpods\s*\w*)', r'(ps5)', r'(switch)', r'(xbox)',
            r'(ryzen\s*\d+)', r'(i[3579]-\d+)', r'(rx\s*\d+)'
        ]
        for pattern in model_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                tag = match.strip().upper()
                if tag and tag not in tags:
                    tags.append(tag)

        return {
            'tags': tags[:8],
            'source': 'keyword'
        }


class ContentFilter:
    SENSITIVE_WORDS = [
        '作弊', '骗子', '假货', '诈骗', '钓鱼',
        '色情', '赌博', '暴力', '毒品', '枪支'
    ]

    @staticmethod
    def contains_sensitive(text):
        text_lower = text.lower()
        found = []
        for word in ContentFilter.SENSITIVE_WORDS:
            if word in text_lower:
                found.append(word)
        return {
            'is_clean': len(found) == 0,
            'found_words': found
        }

    @staticmethod
    def filter_text(text):
        result = ContentFilter.contains_sensitive(text)
        if result['is_clean']:
            return {'filtered': False, 'text': text}
        return {'filtered': True, 'text': text}


class AIMessageSummarizer:
    @staticmethod
    def summarize(message_content):
        if not message_content:
            return ''

        content = message_content.strip()

        if len(content) <= 50:
            return content

        return content[:50] + '...'


def generate_conversation_hash(user1_id, user2_id):
    sorted_ids = sorted([str(user1_id), str(user2_id)])
    return hashlib.md5('_'.join(sorted_ids).encode()).hexdigest()


def format_timestamp(dt=None):
    if dt is None:
        dt = datetime.now()
    return dt.strftime('%Y-%m-%d %H:%M:%S')
