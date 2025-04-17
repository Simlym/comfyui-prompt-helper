import os
import json
import requests
from typing import Dict, Any, List
from openai import OpenAI
import httpx

class PromptProcessor:
    """
    提示词处理节点
    将中文提示词转换为适合不同模型的英文提示词，并生成对应的中文翻译
    """
    
    def __init__(self):
        self.client = None
        self.conversation_history = []
        self.config = self._load_config()
        self.providers = self._get_providers()
        self.models = self._get_models()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return {
                "providers": {},
                "default_provider": "",
                "default_model": "",
                "settings": {
                    "auto_save_api_key": False
                }
            }

    def _get_providers(self) -> List[str]:
        """获取所有供应商名称"""
        return list(self.config.get("providers", {}).keys())

    def _get_models(self) -> List[str]:
        """获取所有模型名称（格式：供应商_模型）"""
        models = []
        for provider, config in self.config.get("providers", {}).items():
            for model_id in config.get("models", []):
                models.append(f"{provider}_{model_id}")
        return models

    def _get_model_display_names(self) -> Dict[str, str]:
        """获取模型显示名称映射"""
        display_names = {}
        for provider, config in self.config.get("providers", {}).items():
            for model_id, model_name in config.get("models", {}).items():
                # 使用供应商名称和模型显示名称的组合
                display_names[f"{provider}_{model_id}"] = f"{model_name}"
        return display_names

    @classmethod
    def INPUT_TYPES(s):
        # 创建实例以访问配置
        instance = s()
        models = instance._get_models()
        
        return {
            "required": {
                "chinese_prompt": ("STRING", {
                    "multiline": True,
                    "default": "请输入中文提示词",
                }),
                "sd_model_type": (["SD1.5", "SDXL", "FLUX"],),
                "model": (models,),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "你是一个ComfyUI专家，擅长将中文提示词转换为适合不同模型的英文提示词。请根据用户指定的模型类型，生成最适合的英文提示词，并确保中文翻译准确对应英文内容。同时，请生成相应的负向提示词。",
                }),
                "api_key": ("STRING", {
                    "multiline": False,
                    "default": "",
                }),
                "use_context": ("BOOLEAN", {
                    "default": False,
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive(en)", "negative(en)", "positive(zhs)", "negative(zhs)")
    FUNCTION = "process_prompt"
    CATEGORY = "conditioning"

    def _init_client(self, model: str, api_key: str = None):
        """初始化客户端"""
        if not self.client:
            # 从模型字符串中提取供应商和模型ID
            provider, model_id = model.split('_')
            provider_config = self.config["providers"].get(provider, {})
            base_url = provider_config.get("base_url", "")
            
            # 优先使用界面输入的API密钥
            if api_key:
                # 如果启用了自动保存，且界面输入的API Key与配置文件中的不同
                if (self.config.get("settings", {}).get("auto_save_api_key", False) and 
                    api_key != provider_config.get("api_key", "")):
                    # 更新配置文件中的API Key
                    self.config["providers"][provider]["api_key"] = api_key
                    self._save_config()
            else:
                # 如果界面没有输入，使用配置文件中的API Key
                api_key = provider_config.get("api_key", "")
            
            if not api_key:
                raise ValueError(f"请提供有效的 {provider} API 密钥")
            
            # 配置代理
            proxy_settings = self.config.get("settings", {}).get("proxy", {})
            proxies = None
            if proxy_settings.get("enabled", False):
                proxies = {
                    "http": proxy_settings.get("http"),
                    "https": proxy_settings.get("https")
                }
            
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                http_client=httpx.Client(proxies=proxies) if proxies else None
            )

    def _save_config(self):
        """保存配置到文件"""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")

    def _build_prompt(self, chinese_prompt: str, sd_model_type: str) -> str:
        return f"""请根据以下中文提示词，完成四个任务：

            1. 生成适合{sd_model_type}模型的正向英文提示词
            2. 将正向英文提示词准确翻译回中文
            3. 生成适合{sd_model_type}模型的负向英文提示词
            4. 将负向英文提示词准确翻译回中文

            原始中文提示词：{chinese_prompt}

            请确保：
            1. 英文提示词要符合{sd_model_type}模型的最佳实践
            2. 保持原始语义的准确性
            3. 使用适当的英文表达方式
            4. 如果涉及艺术风格，使用标准的英文艺术术语
            5. 如果涉及技术参数，使用正确的英文技术术语
            6. 中文翻译要准确对应英文内容，保持专业术语的一致性
            7. 负向提示词要包含常见的负面元素，如低质量、模糊、变形等

            请严格按照以下格式输出，不要添加任何其他内容：
            [正向英文提示词]
            <这里放置正向英文提示词>

            [正向中文翻译]
            <这里放置正向英文提示词的中文翻译>

            [负向英文提示词]
            <这里放置负向英文提示词>

            [负向中文翻译]
            <这里放置负向英文提示词的中文翻译>"""

    def _parse_response(self, response: str) -> tuple:
        """解析API返回的响应，提取英文提示词和中文翻译"""
        print(f"原始响应: {response}")  # 调试信息
        
        positive_english = ""
        positive_chinese = ""
        negative_english = ""
        negative_chinese = ""
        
        # 尝试不同的分隔方式
        if "[正向英文提示词]" in response and "[负向中文翻译]" in response:
            parts = response.split("[负向中文翻译]")
            if len(parts) > 1:
                # 提取负向中文翻译
                negative_chinese = parts[1].strip()
                
                # 提取负向英文提示词
                negative_part = parts[0].split("[负向英文提示词]")
                if len(negative_part) > 1:
                    negative_english = negative_part[1].split("[负向中文翻译]")[0].strip()
                    
                    # 提取正向部分
                    positive_part = negative_part[0].split("[正向中文翻译]")
                    if len(positive_part) > 1:
                        positive_chinese = positive_part[1].strip()
                        
                        # 提取正向英文提示词
                        english_part = positive_part[0].split("[正向英文提示词]")
                        if len(english_part) > 1:
                            positive_english = english_part[1].strip()
        
        print(f"解析结果 - 正向英文: {positive_english}")  # 调试信息
        print(f"解析结果 - 正向中文: {positive_chinese}")   # 调试信息
        print(f"解析结果 - 负向英文: {negative_english}")   # 调试信息
        print(f"解析结果 - 负向中文: {negative_chinese}")   # 调试信息
        
        return positive_english, positive_chinese, negative_english, negative_chinese

    def process_prompt(self, chinese_prompt: str, sd_model_type: str, model: str, 
                      system_prompt: str, api_key: str, use_context: bool) -> tuple:
        """
        处理提示词的主要函数
        """
        # 从模型字符串中提取实际的模型ID
        model_id = model.split('_')[1]
        
        self._init_client(model, api_key)

        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if use_context and self.conversation_history:
            messages.extend(self.conversation_history)

        user_prompt = self._build_prompt(chinese_prompt, sd_model_type)
        messages.append({
            "role": "user",
            "content": user_prompt
        })

        try:
            print(f"发送请求到 {model} API...")  # 调试信息
            response = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            # 解析响应
            positive_english, positive_chinese, negative_english, negative_chinese = self._parse_response(response.choices[0].message.content)
            
            # 更新对话历史
            if use_context:
                self.conversation_history = messages[-2:]  # 只保留最后两条消息
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.choices[0].message.content
                })
            
            return positive_english, negative_english, positive_chinese, negative_chinese
            
        except Exception as e:
            print(f"API 请求失败: {str(e)}")
            return "", "", "", ""

# 节点映射
NODE_CLASS_MAPPINGS = {
    "PromptProcessor": PromptProcessor
}

# 节点显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptProcessor": "Prompt LLM Helper"
}