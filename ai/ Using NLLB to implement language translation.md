## 使用 nllb 实现语言翻译

### 环境介绍

* 基础环境：

  - ```Ubuntu 24.04.2 LTS```
  - ```NVIDIA-SMI 550.120```
  - ```CUDA Version: 12.4```
  - ```Python 3.12.9```

* 依赖版本：

  - ```transformers==4.57.3```
  - ```huggingface-hub==0.36.0```
  - ```torch==2.9.1```
  - ```fastapi==0.127.0```
  - ```uvicorn==0.40.0```

### 实现步骤

* 安装依赖：

  ```bash
  pip install transformers==4.57.3 huggingface-hub==0.36.0 torch==2.9.1 fastapi==0.127.0 uvicorn==0.40.0
  ```

* 编写```web```服务：

  ```python
  import torch
  from fastapi import FastAPI
  from pydantic import BaseModel
  from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

  # =========================
  # 基础配置
  # =========================
  MODEL_NAME = "facebook/nllb-200-distilled-600M"
  DTYPE = torch.float16

  # =========================
  # FastAPI 初始化
  # =========================
  app = FastAPI(
      title="NLLB Translation Service",
      description="Translation service based on facebook/nllb-200-distilled-600M",
      version="1.0.0",
  )

  # =========================
  # 加载模型（全局，只加载一次）
  # =========================
  tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
  model = AutoModelForSeq2SeqLM.from_pretrained(
      MODEL_NAME,
      device_map="auto",
      dtype=DTYPE,
  )

  model.eval()

  # =========================
  # 请求 / 响应数据结构
  # =========================
  class TranslateRequest(BaseModel):
      text: str
      src_lang: str   # 如 rus_Cyrl
      tgt_lang: str   # 如 zho_Hans
      max_new_tokens: int = 64
      num_beams: int = 5


  class TranslateResponse(BaseModel):
      translation: str


  # =========================
  # 翻译接口
  # =========================
  @app.post("/translate", response_model=TranslateResponse)
  def translate(req: TranslateRequest):
      """
      翻译接口
      """
      # 1. 设置源语言
      tokenizer.src_lang = req.src_lang

      # 2. Tokenize
      inputs = tokenizer(
          req.text,
          return_tensors="pt",
          padding=True,
      ).to(model.device)

      # 3. 推理
      with torch.inference_mode():
          outputs = model.generate(
              **inputs,
              forced_bos_token_id=tokenizer.convert_tokens_to_ids(req.tgt_lang),
              max_new_tokens=req.max_new_tokens,
              num_beams=req.num_beams,
              do_sample=False,
          )

      # 4. 解码
      translation = tokenizer.decode(
          outputs[0],
          skip_special_tokens=True
      )

      return TranslateResponse(translation=translation)
  ```

* 启动服务：

  ```bash
  uvicorn app:app --host 0.0.0.0 --port 8000
  ```

* 测试服务：

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Я хочу поехать на Южный железнодорожный вокзал Гуанчжоу.",
    "src_lang": "rus_Cyrl",
    "tgt_lang": "zho_Hans"
  }'
  ```

  输出：

  ```bash
  {"translation": "我想去广州南部火车站"}
  ```

  可使用以下测试用例，对比不同语言之间的翻译效果：

  ```Chinese -> Chinese```:

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我想去广州南站。",
    "src_lang": "zho_Hans",
    "tgt_lang": "zho_Hans"
  }'
  ```

  ```English -> Chinese```:

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I want to go to Guangzhou South Railway Station.",
    "src_lang": "eng_Latn",
    "tgt_lang": "zho_Hans"
  }'
  ```

  ```German -> Chinese```：

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Ich möchte zum Südbahnhof Guangzhou fahren.",
    "src_lang": "deu_Latn",
    "tgt_lang": "zho_Hans"
  }'
  ```

  ```Italian -> Chinese```：

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Voglio andare alla stazione ferroviaria di Guangzhou Sud.",
    "src_lang": "ita_Latn",
    "tgt_lang": "zho_Hans"
  }'
  ```

  ```Portuguese -> Chinese```：

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Quero ir para a Estação Ferroviária Sul de Guangzhou.",
    "src_lang": "por_Latn",
    "tgt_lang": "zho_Hans"
  }'
  ```

  ```Spanish -> Chinese```：

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Quiero ir a la estación de tren sur de Guangzhou.",
    "src_lang": "spa_Latn",
    "tgt_lang": "zho_Hans"
  }'
  ```

  ```Japanese -> Chinese```：

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "広州南駅に行きたいです。",
    "src_lang": "jpn_Jpan",
    "tgt_lang": "zho_Hans"
  }'
  ```

  ```Korean -> Chinese```：

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "저는 광저우 남역에 가고 싶습니다.",
    "src_lang": "kor_Hang",
    "tgt_lang": "zho_Hans"
  }'
  ```

  ```French -> Chinese```：

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Je veux aller à la gare de Guangzhou Sud.",
    "src_lang": "fra_Latn",
    "tgt_lang": "zho_Hans"
  }'
  ```
 
  ```Russian -> Chinese```：

  ```bash
  curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Я хочу поехать на Южный железнодорожный вокзал Гуанчжоу.",
    "src_lang": "rus_Cyrl",
    "tgt_lang": "zho_Hans"
  }'
  ```

### 参考文献

* [facebook/nllb-200-3.3B](https://huggingface.co/facebook/nllb-200-3.3B)
