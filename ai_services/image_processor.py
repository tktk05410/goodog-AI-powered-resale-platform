import cv2
import numpy as np
import base64
import requests

class ImageProcessor:
    @staticmethod
    def read_image(image_path_or_bytes):
        if isinstance(image_path_or_bytes, bytes):
            nparr = np.frombuffer(image_path_or_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            img = cv2.imread(image_path_or_bytes)
        return img

    @staticmethod
    def to_grayscale(img):
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def denoise(img, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21):
        if len(img.shape) == 2:
            return cv2.fastNlMeansDenoising(img, None, h, templateWindowSize, searchWindowSize)
        else:
            return cv2.fastNlMeansDenoisingColored(img, None, h, hColor, templateWindowSize, searchWindowSize)

    @staticmethod
    def detect_edges(img, threshold1=50, threshold2=150):
        gray = ImageProcessor.to_grayscale(img)
        return cv2.Canny(gray, threshold1, threshold2)

    @staticmethod
    def resize_image(img, max_dimension=800):
        height, width = img.shape[:2]
        max_dim = max(height, width)
        scale = max_dimension / max_dim
        if scale < 1:
            return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        return img

    @staticmethod
    def extract_histogram(img, bins=256):
        gray = ImageProcessor.to_grayscale(img)
        hist = cv2.calcHist([gray], [0], None, [bins], [0, bins])
        hist = hist.flatten()
        hist = hist / hist.sum()
        return hist

    @staticmethod
    def extract_features(img):
        gray = ImageProcessor.to_grayscale(img)

        hist = ImageProcessor.extract_histogram(gray)

        features = {
            'mean_intensity': float(np.mean(gray)),
            'std_intensity': float(np.std(gray)),
            'contrast': float(np.max(gray) - np.min(gray)),
            'entropy': float(-np.sum(hist * np.log2(hist + 1e-10)))
        }

        return features

    @staticmethod
    def compare_histograms(hist1, hist2):
        return cv2.compareHist(hist1.astype(np.float32), hist2.astype(np.float32), cv2.HISTCMP_CORREL)

    @staticmethod
    def image_to_base64(img):
        _, buffer = cv2.imencode('.jpg', img)
        return base64.b64encode(buffer).decode('utf-8')

    @staticmethod
    def recognize_with_qwen(image_input, api_key, base_url=None):
        base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"

        try:
            img = ImageProcessor.read_image(image_input)
            if img is None:
                return {'tags': ['图片'], 'source': 'fallback'}

            img = ImageProcessor.resize_image(img, max_dimension=1024)
            base64_image = ImageProcessor.image_to_base64(img)

            url = f"{base_url}/chat/completions"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            data = {
                'model': 'qwen3.7-plus',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': '请识别这张图片中的物品，并生成3-5个合适的二手市场标签。只返回JSON数组格式，例如：["电子产品", "手机", "九成新"]。不要返回任何其他内容。'
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{base64_image}'
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': 200
            }

            response = requests.post(url, json=data, headers=headers, timeout=15)
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content'].strip()
                import json
                tags = json.loads(content)
                if isinstance(tags, list):
                    return {
                        'tags': tags[:5],
                        'source': 'qwen-vision'
                    }

        except Exception as e:
            print(f'Qwen vision recognition error: {e}')

        return {'tags': ['二手商品'], 'source': 'fallback'}