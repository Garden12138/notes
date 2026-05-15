## 实现自注意力

### 长序列建模的问题

* 在研究长序列建模问题之前，我们要从刚开始的模型架构说起，以语言翻译的翻译模型为例：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm16.png)

  翻译时，不可能逐词翻译，实际上翻译过程中是需要上下文的理解和语法的对齐。为了解决这一局限性，模型包含了两个子模块的深度神经网络，即所谓的编码器（```encoder```）和解码器（```decoder```）。编码器的任务是先读取并处理整个文本，然后解码器生成翻译后的文本，即```RNN```模型：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm17.png)

  编码器部分将整个输入文本处理为一个隐藏状态（记忆单元）。解码器随后使用最终隐藏状态生成输出。这个架构有个重大问题和限制在于在解码阶段 ```RNN``` 无法直接访问编码器的早期隐藏状态。因此，它只能依赖当前隐藏状态来封装所有相关信息。这种设计可能导致上下文信息的丢失，特别是在依赖关系较长的复杂句子中，这一问题尤为突出。如有一个长句子：```“The cat, who was sitting on the windowsill, jumped down because it saw a bird flying outside the window.”```要理解```“it”```指的是```“the cat”```而不是```“the windowsill”```或其他内容。对于 ```RNN``` 来说，这个任务是有难度的，因为：

    * 长距离依赖问题：在 ```RNN``` 中，每个新输入的词会被依次传递到下一个时间步。随着句子长度增加，模型的隐状态会不断被更新，但早期信息（如```“the cat”```）会在层层传播中逐渐消失。因此，模型可能无法在```“it”```出现时有效地记住```“the cat”```是```“it”```的指代对象。
    * 梯度消失问题：```RNN``` 在反向传播（根据损失值计算梯度的过程）中的梯度会随着时间步的增加逐渐减小，这种“梯度消失”（```RNN``` 的链式结构导致反向传播要跨很多时间步传递梯度；如果每一步梯度都被缩小，传到前面时就几乎没了，这就是梯度消失）使得模型很难在长句中保持信息的准确传播，从而难以捕捉到长距离的语义关联。

  为了弥补 ```RNN``` 的这些不足，注意力机制被引入。它的关键思想是在处理每个词时，不仅依赖于最后的隐藏状态，而是允许模型直接关注序列中的所有词。这样，即使是较远的词也能在模型计算当前词的语义时直接参与。假设使用一个简单的注意力矩阵，模型在处理```“it”```时，给每个词的权重可能如下：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm18.png)

  在这个注意力矩阵中，可以看到```“it”```对```“the cat”```有较高的关注权重（0.3），而对其他词的关注权重较低。这种直接的关注能力让模型能够高效捕捉长距离依赖关系，理解```“it”```与```“the cat”```的语义关联。
    
    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm19.png)

### 通过注意力机制捕捉数据依赖关系

* ```RNN```模型在长序列中存在消息覆盖或丢失的建模问题，通过引入注意力机制对编码器-解码器架构的 ```RNN``` 进行了改进，使得解码器在每个解码步骤可以选择性地访问输入序列的不同部分：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm20.png)

  后续研究发现构建用于自然语言处理的深度神经网络并不需要 ```RNN``` 结构，随后提出了基于自注意力机制的原始 ```Transformer``` 架构。自注意力机制是一种允许输入序列中的每个位置在计算序列表示时关注同一序列中所有位置的机制。自注意力机制是基```Transformer```架构的当代大语言模型（如```GPT```系列模型）的关键组成部分。

### 通过自注意力机制关注输入的不同部分

* 在自注意力机制中，```“self”```指的是该机制通过关联同一输入序列中的不同位置来计算注意力权重的能力。它评估并学习输入内部各部分之间的关系和依赖性。

* 不含可训练权重的简化自注意力机制。实现没有包含任何可训练的权重简化自注意力机制，目标是为输入序列每个元素计算一个上下文向量（代表该元素与其他元素的关联关系）：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm21.png)

  以输入序列```Your journey starts with one step```为例：

  ```python
  import torch
  inputs = torch.tensor(
    [[0.43, 0.15, 0.89], # Your     (x^1)
     [0.55, 0.87, 0.66], # journey  (x^2)
     [0.57, 0.85, 0.64], # starts   (x^3)
     [0.22, 0.58, 0.33], # with     (x^4)
     [0.77, 0.25, 0.10], # one      (x^5)
     [0.05, 0.80, 0.55]] # step     (x^6)
  print('初始化输入嵌入层:')
  print(inputs.shape)
  ```

  首先，计算注意力得分ω，通过计算查询 ```x(2)``` 与每个其他输入 ```token``` 的点积（点积运算本质上是一种将两个向量按元素相乘后再求和的简单方式）：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm22.png)

  ```python
  # 计算输入序列第二个元素的注意力得分
  query = inputs[1]
  attn_scores_2 = torch.empty(inputs.shape[0])
  for i, x_i in enumerate(inputs):
      attn_scores_2[i] = torch.dot(x_i, query)
  print(attn_scores_2) 
  ```

  接下来，对计算的每个注意力得分进行归一化（注意力权重之和为 1，有助于解释和保持LLM训练稳定性）：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm23.png)

  ```python
  # 输入序列第二个元素的注意力得分归一，方式1：直接除法
  attn_weights_2_tmp = attn_scores_2 / attn_scores_2.sum()
  print("输入序列第二个元素的注意力得分归一，方式1：直接除法")
  print("Attention weights:", attn_weights_2_tmp)
  print("Sum:", attn_weights_2_tmp.sum())
  # 输入序列第二个元素的注意力得分归一，方式2：自定义softmax算法
  def softmax_naive(x):
      return torch.exp(x) / torch.exp(x).sum(dim=0)
  attn_weights_2_naive = softmax_naive(attn_scores_2)
  print("输入序列第二个元素的注意力得分归一，方式2：自定义softmax算法")
  print("Attention weights:", attn_weights_2_naive)
  print("Sum:", attn_weights_2_naive.sum())
  # 输入序列第二个元素的注意力得分归一，方式2：torch.softmax函数
  attn_weights_2 = torch.softmax(attn_scores_2, dim=0)
  print("输入序列第二个元素的注意力得分归一，方式2：torch.softmax函数")
  print("Attention weights:", attn_weights_2)
  print("Sum:", attn_weights_2.sum())
  ```

  使用```softmax```好处：
    * 归一化输出为概率：```Softmax``` 将输出转换为 0 到 1 之间的概率，且所有类别的概率之和为 1，方便解释结果。例如，在分类任务中，输出可以直接表示模型对各类别的信心。
    * 平滑和放大效果：```Softmax``` 不仅能归一化，还具有平滑和放大效果。较大的输入值会被放大，较小的输入值会被抑制，从而增强模型对最优类别的区分。
    * 支持多分类问题：与 ```sigmoid``` 不同，```Softmax``` 适用于多类别分类问题。它可以输出每个类别的概率，使得模型可以处理多分类任务。

  最后，通过加权和（将每个输入向量与对应的归一后的注意力得分相乘后相加）计算输入元素的上下文向量：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm24.png)

  ```python
  # 使用加权和计算输入序列第二个元素的的上下文向量
  context_vec_2 = torch.zeros(query.shape)
  for i,x_i in enumerate(inputs):
      context_vec_2 += attn_weights_2[i]*x_i
  print("输入序列第二个元素的的上下文向量")
  print(context_vec_2)
  ```

* 为所有输入的 ```token``` 计算注意力权重。在上一步我们实现了计算输入序列第二个元素的上下文向量，在这基础上，我们可实现所有输入对的上下问向量计算，流程和上一步一致：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm25.png)

  首先，初始化定义所有输入对的注意力的得分张量：

  ```python
  attn_scores = torch.empty(inputs.shape[0], inputs.shape[0])
  ```

  接下来，计算所有输入对的点积：

  ```python
  # 使用嵌套for循环计算点积
  for i, x_i in enumerate(inputs):
      for j, x_j in enumerate(inputs):
          attn_scores[i, j] = torch.dot(x_i, x_j)
  print("使用嵌套for循环计算点积:")
  print(attn_scores)
  # 使用矩阵乘法计算点积
  attn_scores = inputs @ inputs.T
  print("使用矩阵乘法计算点积:")
  print(attn_scores)
  ```

  继续计算所有输入对的注意力权重

  ```python
  # 计算所有输入对的注意力权重（归一）
  attn_weights = torch.softmax(attn_scores, dim=-1)
  print("计算所有输入对的注意力权重（归一）:")
  print(attn_weights)
  ```

  最后计算所有输入对的上下文向量：

  ```python
  # 计算所有输入对的上下文向量，使用矩阵乘法
  all_context_vecs = attn_weights @ inputs
  print("计算所有输入对的上下文向量，使用矩阵乘法：:")
  print(all_context_vecs)
  ```

  符号```@```表示矩阵乘法运算；```.T```表示矩阵转置运算；```dim=-1```表示沿着最后一维进行运算，当前张量是二维，-1表示列，即沿着列方向（水平方向归一）。

### 实现带有可训练权重的自注意力机制

### 使用因果注意力机制来屏蔽后续词

### 从单头注意力扩展到多头注意力