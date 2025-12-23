## 使用 fastText 实现语言识别

### 介绍

* ```fastText```是由```Facebook AI```研究室（```FAIR```）在 2016 年开源的一个高效、轻量级的深度学习库，专门用于文本分类和词表示学习（词向量生成）。其官方提供了包含 157 种语言的预训练模型，所以我们可以用于语言识别。

### 实现步骤

* 按顺序安装依赖：

  ```bash
  conda create -n fasttext python=3.10
  conda activate fasttext
  pip install numpy==1.26.4 fasttext fastapi fasttext
  ```

  由于```numpy```版本较低，建议使用```conda```环境隔离。

* 下载官方模型：

  ```bash
  wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin
  ```

* 编写```web```服务：

  ```python
  import fasttext
  from fastapi import FastAPI, HTTPException
  from pydantic import BaseModel

  MODEL_PATH = "lid.176.bin"

  app = FastAPI(
      title="Language Detection Service",
      description="Language detection based on fastText lid.176",
      version="1.0.0",
  )

  # -------- 模型全局加载（只加载一次） --------
  try:
      model = fasttext.load_model(MODEL_PATH)
  except Exception as e:
      raise RuntimeError(f"Failed to load fastText model: {e}")


  # -------- 请求 / 响应模型 --------
  class DetectRequest(BaseModel):
      text: str


  class DetectResponse(BaseModel):
      language: str
      confidence: float


  # -------- 核心逻辑 --------
  def detect_language(text: str):
      labels, probs = model.predict(text, k=1)
      lang = labels[0].replace("__label__", "")
      confidence = float(probs[0])
      return lang, confidence


  # -------- API 接口 --------
  @app.post("/detect", response_model=DetectResponse)
  def detect(req: DetectRequest):
      if not req.text or not req.text.strip():
          raise HTTPException(status_code=400, detail="text must not be empty")

      lang, conf = detect_language(req.text)

      return DetectResponse(
          language=lang,
          confidence=conf,
      )


  # -------- 健康检查 --------
  @app.get("/health")
  def health():
      return {"status": "ok"}
  ```

* 运行```web```服务：

  ```bash
  uvicorn app:app --host 0.0.0.0 --port 8000
  ```

  注意：服务代码文件以```app.py```命名。

* 测试```web```服务：

  ```bash
  curl -X POST "http://localhost:8000/detect" \
     -H "Content-Type: application/json" \
     -d '{"text": "我想去广州南站。"}'
  ```

  输出：

  ```bash
  {"language":"zh","confidence":0.9967644214630127}
  ```

### 识别语种

* 目前对于以下语言的识别准确度较高：

  ```bash
  Chinese    -> zh, confidence=0.997, text=我想去广州南站。
  English    -> en, confidence=0.962, text=I want to go to Guangzhou South Railway Station.
  German     -> de, confidence=1.000, text=Ich möchte zum Südbahnhof Guangzhou fahren.
  Italian    -> it, confidence=0.996, text=Voglio andare alla stazione ferroviaria di Guangzhou Sud.
  Portuguese -> pt, confidence=0.966, text=Quero ir para a Estação Ferroviária Sul de Guangzhou.
  Spanish    -> es, confidence=0.981, text=Quiero ir a la estación de tren sur de Guangzhou.
  Japanese   -> ja, confidence=1.000, text=広州南駅に行きたいです。
  Korean     -> ko, confidence=1.000, text=저는 광저우 남역에 가고 싶습니다.
  French     -> fr, confidence=0.997, text=Je veux aller à la gare de Guangzhou Sud.
  Russian    -> ru, confidence=0.998, text=Я хочу поехать на Южный железнодорожный вокзал Гуанчжоу.
  ```