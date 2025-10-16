## 营业执照OCR实现

### 需求背景

* 业务系统需要在上传完营业执照后，自动识别出营业执照上的信息，并将其自动填写在业务表单中保存起来，暂时只需要统一社会信用代码、名称、法定代表人、住所这四个字段。

### 方案设计

* 部署读光-票证检测矫正模型，对于翻转、倾斜或者模糊不清的营业执照图片，模型能够自动矫正，提升识别准确率。
* 部署```Nanonets-OCR-s```模型，参数小，识别准确率高，能够识别出营业执照上的信息。
* 使用```FastAPI框架搭建RESTful API```，接收上传的营业执照图片以及矫正标识，若需要矫正，则先调用矫正模型，矫正后再调用模型进行识别，返回识别结果。

### 代码示例

* [Business-License-OCR](https://github.com/Garden12138/ai-example/tree/main/Business-License-OCR)

### 可优化事项

* 不依赖矫正标识，可以自动识别图片是否矫正。

### 参考文献

* [读光-票证检测矫正模型](https://www.modelscope.cn/models/iic/cv_resnet18_card_correction)
* [Nanonets-OCR-s](https://www.modelscope.cn/models/nanonets/Nanonets-OCR-s)