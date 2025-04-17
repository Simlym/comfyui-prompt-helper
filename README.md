# ComfyUI Prompt Helper

一个 ComfyUI 自定义节点，用于处理中文提示词，生成适合不同模型的英文提示词及其翻译。

## 功能特点

- 支持多种模型类型（SD1.5、SDXL、FLUX）
- 支持多个 API 提供商（DeepSeek、OpenAI 等）
- 生成正向和负向提示词
- 提供中英文翻译
- 支持上下文关联
- 可配置的 API 密钥管理

## 安装

1. 将本仓库克隆到 ComfyUI 的 `custom_nodes` 目录：
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/your-username/comfyui-prompt-helper.git
```

2. 安装依赖：
```bash
cd comfyui-prompt-helper
pip install -r requirements.txt
```

## 配置

编辑 `config.json` 文件，配置 API 密钥和其他设置：

```json
{
    "providers": {
        "DeepSeek": {
            "base_url": "https://api.deepseek.com",
            "api_key": "your_api_key_here",
            "models": [
                "deepseek-chat",
                "deepseek-reasoner"
            ]
        }
    },
    "default_provider": "DeepSeek",
    "default_model": "deepseek-chat",
    "settings": {
        "auto_save_api_key": false,
        "proxy": {
            "enabled": false,
            "http": "http://127.0.0.1:10808",
            "https": "http://127.0.0.1:10808"
        }
    }
}
```

## 使用方法

1. 在 ComfyUI 界面中找到 "提示词处理" 类别
2. 添加 "提示词处理器" 节点
3. 输入中文提示词
4. 选择模型类型和 API 模型
5. 可选：输入 API 密钥（如果与配置文件中的不同）
6. 可选：启用上下文关联
7. 运行工作流

## 输出

节点会生成四个输出：
- positive text(EN): 正向英文提示词
- negative text(EN): 负向英文提示词
- positive text(ZHS): 正向中文翻译
- negative text(ZHS): 负向中文翻译

## 注意事项

- 确保已正确配置 API 密钥
- 如果使用代理，请在配置文件中启用并设置代理地址
- API 密钥的优先级：界面输入 > 配置文件

## 许可证

MIT 