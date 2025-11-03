## AI视频换脸实现方式

### 背景

* 应运营业务需求，需调研视频换脸技术，了解不同视频换脸技术的优缺点，以及如何选择合适的技术方案。通过对现在市面上大模型的调研，发现```Wan2.2-Animate```模型是目前最优秀的视频换脸模型。基于此模型进行多种视频换脸实现方式的探索。

### 实现方式

* [```Huggigng Face```的```Wan2.2-Animate```模型运行空间](https://huggingface.co/spaces/Wan-AI/Wan2.2-Animate)：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/huggingface-wan2.2animate-lb-wlq.png)

  优点：可以体验模型最直接的效果。
  
  缺点：需翻墙，生成视频时间长，对于上传的图片有敏感性限制，如```Donald John Trump```上传的图片会报错，生成的视频里对于人除外的场景会出现瑕疵，如马赛克。

* [```ModelScope```的```Wan2.2-Animate```模型运行空间](https://huggingface.co/spaces/Wan-AI/Wan2.2-Animate)：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/modelscope-wan2.2animate-lb-wlq.png)

  优点：可以体验模型最直接的效果，不需翻墙。
  
  缺点：生成视频时间长，对于上传的图片有敏感性限制，如```Donald John Trump```上传的图片会报错，生成的视频里对于人除外的场景会出现瑕疵，如马赛克。

* [```Wan```产品平台](https://create.wan.video/generate/avatar/character-swap?model=wan2.2)：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/wancreatevideo-wan2.2characterswap-lb-wlq.png)

  优点：可以体验模型产品化的效果。
  
  缺点：生成视频需排队等待，对于上传的图片有敏感性限制，如```Donald John Trump```上传的图片会报错，生成的视频里对于人除外的场景会出现瑕疵，如马赛克。

* [```ComfyUI```产品在线平台](https://www.runninghub.cn/)：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/runninghub-wan2.2animateworkflow-lb-wlq1.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/runninghub-wan2.2animateworkflow-lb-wlq2.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/runninghub-wan2.2animateworkflow-lb-wlq3.png)

  如果```Background Masking```节点生成的背景遮罩不合适，可以手动调整，绿色圈代表人物，红色圈代表背景。
  
  优点：可自定义调整人物背景遮罩，生成视频时间短（5秒视频4分钟以内生成），质量高，上传的图片没有限制。
  
  缺点：生成视频需排队等待。

* [```ComfyUI```本地部署平台](https://www.comfy.org/zh-cn/)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/comfyui-local.png)

  部署成功后，可参考[零基础教程】如何运行别人的ComfyUI工作流](https://aisc.chinaz.com/jiaocheng/10408.html)导入[```wanvideo_WanAnimate_角色替换工作流```](https://github.com/Garden12138/ai-example/blob/main/ComfyUI-Workflow/wanvideo_WanAnimate_%E8%A7%92%E8%89%B2%E6%9B%BF%E6%8D%A2%E5%B7%A5%E4%BD%9C%E6%B5%81.json)，主要是进行```Install Missing Custom Nodes```操作，安装缺失的自定义节点还有下载安装模型，模型与文件放置如下：

    * ```Diffusion```模型放入```ComfyUI/models/diffusion_models/```，[此工作流使用的模型为```Kijai/WanVideo_comfy_fp8_scaled```](https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/tree/main/Wan22Animate)
    * 文本编码器（如```umt5_xxl…```）：放入```ComfyUI/models/text_encoders/```，[此工作流使用的模型为```umt5-xxl-enc-bf16.safetensors```](https://huggingface.co/Kijai/WanVideo_comfy/blob/main/umt5-xxl-enc-bf16.safetensors)
    * ```VAE```：放入```ComfyUI/models/vae/```，[此工作流使用的模型为```Wan2_1_VAE_bf16.safetensors```](https://huggingface.co/Kijai/WanVideo_comfy/blob/main/Wan2_1_VAE_bf16.safetensors)
    * ```LORA```：放入```ComfyUI/models/loras/```，[此工作流使用的模型为```Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank128_bf16.safetensors```](https://huggingface.co/Kijai/WanVideo_comfy/blob/main/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank128_bf16.safetensors)，还有[```LoRAs/Wan22_relight/WanAnimate_relight_lora_fp16.safetensors```](https://huggingface.co/Kijai/WanVideo_comfy/blob/main/LoRAs/Wan22_relight/WanAnimate_relight_lora_fp16.safetensors)

  更新完节点和模型后，重启```ComfyUI```服务，即可运行[```wanvideo_WanAnimate_角色替换工作流```](https://github.com/Garden12138/ai-example/blob/main/ComfyUI-Workflow/wanvideo_WanAnimate_%E8%A7%92%E8%89%B2%E6%9B%BF%E6%8D%A2%E5%B7%A5%E4%BD%9C%E6%B5%81.json)。

### 备注说明

* ```ComfyUI```本地部署平台方式目前只在本地```MAC```上部署过，但是运行报错，调整为```MAC```的```MPS```推理还存在各种问题，建议使用```NVIDIA GPU```机器部署，这台机器最好配置能```24～48G```的```4090```显卡。  

### 参考文献

* [Wan2.2-Animate使用全攻略（ComfyUI/在线体验/参数建议）](https://www.laogou717.com/2025/09/21/AI%20era/Wan/Wan2.2-Animate/index.html)