import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

# 避免导入根目录的 app.py
import importlib.util
spec = importlib.util.spec_from_file_location("app", os.path.join(backend_dir, "app.py"))
app_module = importlib.util.module_from_spec(spec)
sys.modules['app'] = app_module
spec.loader.exec_module(app_module)

create_app = app_module.create_app
db = app_module.db
Product = app_module.Product
Tag = app_module.Tag
ProductTag = app_module.ProductTag

def batch_generate_tags():
    app = create_app('development')
    
    with app.app_context():
        products = Product.query.all()
        print(f'找到 {len(products)} 个商品')
        
        for product in products:
            print(f'\n处理商品: {product.title} (ID: {product.id})')
            
            existing_tags = ProductTag.query.filter_by(product_id=product.id).all()
            if existing_tags:
                print(f'  已有 {len(existing_tags)} 个标签，跳过')
                continue
            
            text_tags = []
            image_tags = []
            
            try:
                from ai_services.text_classifier import TextClassifier
                classifier = TextClassifier()
                text_result = classifier.generate_tags_with_qwen(product.title, product.description)
                text_tags = text_result.get('tags', [])
                print(f'  文本分析标签: {text_tags}')
            except Exception as e:
                print(f'  文本分析失败: {e}')
            
            if product.image_path:
                try:
                    from ai_services.image_processor import ImageProcessor
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_path)
                    if os.path.exists(image_path):
                        from ai_services.text_classifier import TextClassifier
                        classifier = TextClassifier()
                        image_result = ImageProcessor.recognize_with_qwen(
                            image_path,
                            classifier.api_key,
                            classifier.base_url
                        )
                        image_tags = image_result.get('tags', [])
                        print(f'  图像识别标签: {image_tags}')
                except Exception as e:
                    print(f'  图像识别失败: {e}')
            
            category = text_tags[0] if text_tags else None
            all_tags = text_tags + [t for t in image_tags if t not in text_tags]
            if category and all_tags and all_tags[0] != category:
                all_tags = [category] + [t for t in all_tags if t != category]
            all_tags = all_tags[:8]
            
            for tag_name in all_tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name, color='#409eff', is_ai_generated=True)
                    db.session.add(tag)
                    db.session.flush()
                
                existing = ProductTag.query.filter_by(product_id=product.id, tag_id=tag.id).first()
                if not existing:
                    product_tag = ProductTag(
                        product_id=product.id,
                        tag_id=tag.id,
                        is_ai_generated=True
                    )
                    db.session.add(product_tag)
            
            db.session.commit()
            print(f'  成功添加 {len(all_tags)} 个标签')
        
        print('\n批量标签生成完成！')

if __name__ == '__main__':
    batch_generate_tags()
