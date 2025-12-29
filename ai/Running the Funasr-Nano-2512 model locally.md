## 本地运行 Funasr-Nano-2512 模型

### 模型介绍

* ```Fun-ASR-Nano-2512```是一款基于数千万小时真实语音数据训练的端到端语音识别大模型。支持低延迟实时转写，覆盖31种语言。

* 模型核心功能：

  * 准确识别远场高噪声环境下的语音。
  * 支持7种中文方言和26种地区口音。
  * 支持31种国际语言，支持多语言的自由切换和混合识别。
  * 音乐背景下的歌词识别。

### 环境准备

* 基础环境：

  - ```Ubuntu 24.04.2 LTS```
  - ```NVIDIA-SMI 550.120```
  - ```CUDA Version: 12.4```
  - ```Python 3.12.9```
  - ```ffmpeg```

* 依赖版本：

  - ```transformers==4.57.3```
  - ```modelscope==1.33.0```
  - ```torch==2.9.1```
  - ```torchaudio==2.9.1```
  - ```torchcodec==0.9.1```
  - ```funasr==1.2.9```

### 运行步骤

* 安装依赖：

  ```bash
  pip install transformers==4.57.3 modelscope==1.33.0 torch==2.9.1 torchaudio==2.9.1 torchcodec==0.9.1 funasr==1.2.9
  ```

* 下载远程调用代码：

  ```bash
  wget https://raw.githubusercontent.com/FunAudioLLM/Fun-ASR/main/model.py
  ```

* 编写运行代码```run.py```：
  
  ```python
  from funasr import AutoModel

  def main():
      model_dir = "FunAudioLLM/Fun-ASR-Nano-2512"
      wav_path = "别来无恙.m4a"
      model = AutoModel(
          model=model_dir,
          trust_remote_code=True,
          vad_model="fsmn-vad",
          vad_kwargs={"max_single_segment_time": 30000},
          remote_code="./model.py",
          device="cuda:0",
      )
      res = model.generate(input=[wav_path], cache={}, batch_size=1)
      text = res[0]["text"]
      print(text)


  if __name__ == "__main__":
      main()
  ```

* 上传音频文件，如```别来无恙.m4a```。

* 运行代码：

  ```bash
  python run.py
  ```

  输出：

  ```bash
  funasr version: 1.2.9.
  Check update of funasr, and it would cost few times. You may disable it by set `disable_update=True` in AutoModel
  You are using the latest version of funasr-1.2.9
  Downloading Model from https://www.modelscope.cn to directory: /home/andy/.cache/modelscope/hub/models/FunAudioLLM/Fun-ASR-Nano-2512
  2025-12-29 11:43:38,250 - modelscope - INFO - Got 1 files, start to download ...
  Downloading [config.yaml]: 100%|████████████████████████████████████████████████| 3.07k/3.07k [00:00<00:00, 11.6kB/s]
  Processing 1 items: 100%|█████████████████████████████████████████████████████████| 1.00/1.00 [00:00<00:00, 3.66it/s]
  2025-12-29 11:43:38,524 - modelscope - INFO - Download model 'FunAudioLLM/Fun-ASR-Nano-2512' successfully.
  WARNING:root:trust_remote_code: True
  Loading remote code successfully: ./model.py
  Downloading Model from https://www.modelscope.cn to directory: /home/andy/.cache/modelscope/hub/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch
  WARNING:root:trust_remote_code: False
  rtf_avg: 0.011: 100%|██████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  2.54it/s]
    0%|                                                                                          | 0/3 [00:00<?, ?it/s]
  The attention mask and the pad token id were not set. As a consequence, you may observe unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results.
  Setting `pad_token_id` to `eos_token_id`:151645 for open-end generation.
  The attention mask is not set and cannot be inferred from input because pad token is same as eos token. As a consequence, you may observe unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results.
  {'load_data': '0.000', 'extract_feat': '0.002', 'forward': '0.340', 'batch_size': '1', 'rtf': '0.113'}, :  33%|▎| 1/3The attention mask and the pad token id were not set. As a consequence, you may observe unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results.
  Setting `pad_token_id` to `eos_token_id`:151645 for open-end generation.
  {'load_data': '0.000', 'extract_feat': '0.002', 'forward': '0.202', 'batch_size': '1', 'rtf': '0.064'}, :  67%|▋| 2/3The attention mask and the pad token id were not set. As a consequence, you may observe unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results.
  Setting `pad_token_id` to `eos_token_id`:151645 for open-end generation.
  rtf_avg: 0.062: 100%|██████████████████████████████████████████████████████████████████| 3/3 [00:02<00:00,  1.35it/s]
  rtf_avg: 0.061, time_speech:  36.928, time_escape: 2.235: 100%|████████████████████████| 1/1 [00:02<00:00,  2.39s/it]
  千辛万苦，忘不了你的模样，忘不了的遍体鳞伤，成为我的力量，忘不了眼神里的光，常在我心上，当我又回头张望，提醒我坚强，用真遗忘他。 的人常在我。 心伤。
  ```

### 参考文献

* [FunAudioLLM/Fun-ASR-Nano-2512](https://www.modelscope.cn/models/FunAudioLLM/Fun-ASR-Nano-2512)