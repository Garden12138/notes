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

* 与简化自注意力机制相比，不是直接使用嵌入向量来计算上下文向量，而是使用可训练的权重参数矩阵来计算上下文向量。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm30.png)

* 逐步计算注意力权重

  * 计算查询向量 ```q``` 、键向量 ```k``` 以及值向量 ```v``` ：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm26.png)

    以输入序列第二个元素为例子：

    ```python
    # 初始化权重参数矩阵
    d_in = inputs.shape[1]                                          
    d_out = 2   
    torch.manual_seed(123)
    W_query = torch.nn.Parameter(torch.rand(d_in, d_out), requires_grad=False)
    W_key   = torch.nn.Parameter(torch.rand(d_in, d_out), requires_grad=False)
    W_value = torch.nn.Parameter(torch.rand(d_in, d_out), requires_grad=False)
    print("初始化权重参数矩阵:")
    print(W_query)
    print(W_key)
    print(W_value)
    # 计算输入序列第二个元素的query、key 和 value 向量
    x_2 = inputs[1]
    query_2 = x_2 @ W_query
    key_2 = x_2 @ W_key
    value_2 = x_2 @ W_value
    print("计算输入序列第二个元素的query、key 和 value 向量:")
    print(query_2)
    print(key_2)
    print(value_2)
    ```

    ```d_out``` 表示输出维度，一般由实际训练时定义，它可将输入维度转化为指定输出维度；这里将```requires_grad```设置为```False```，以便在输出结果中减少不必要的信息，从而使演示更加清晰。但如果要将这些权重矩阵用于模型训练，则需要将```requires_grad```设置为```True```，以便在模型训练过程中更新这些矩阵。

  * 计算注意力得分：
    
    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm27.png)

    以输入序列第二个元素对所有输入元素的注意力得分为例：

    ```python
    # 计算输入序列所有元素的query、key 向量
    querys = inputs @ W_query
    keys = inputs @ W_key
    # 计算输入序列第二个元素对所有输入元素的注意力得分
    print("计算输入序列第二个元素对所有输入元素的注意力得分：")
    attn_scores_2 = querys[1] @ keys.T
    print(attn_scores_2)
    ```

  * 计算注意力权重：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm28.png)

    以输入序列第二个元素对所有输入元素的注意力权重为例：

    ```python
    # 计算输入序列第二个元素对所有输入元素的注意力权重（得分归一）
    print("计算输入序列第二个元素对所有输入元素的注意力权重（得分归一）：")
    d_k = keys.shape[-1]
    attn_weights_2 = torch.softmax(attn_scores_2 / d_k**0.5, dim=-1) # 先进行点积缩放，防止点积结果过大导致梯度丢失
    print(attn_weights_2)
    ```

    使用```sqrt(d_k)```是因为点积结果的大小，通常会随着维度```d_k```增大而变大；更准确地说，它的标准差大约会按```sqrt(d_k)```增大。所以用```sqrt(d_k)```缩放，是为了把点积结果拉回到一个比较稳定的范围。

  * 计算上下文向量：

    ```python
    # 计算输入序列所有元素的向量
    values = inputs @ W_value
    # 计算输入序列第二个元素对所有输入元素的上下文向量
    print("计算输入序列第二个元素对所有输入元素的上下文向量：")
    context_vec_2 = attn_weights_2 @ values
    print(context_vec_2)
    ```

* 实现一个简洁的自注意力机制 Python 类

  * 在上面分步骤展示从嵌入向量到上下文向量每个环节的细节后，我们需要进行整合封装，实现一个简洁的自注意力机制 Python 类。

  * 实现一个简洁的自注意力机制V1类：

    ```python
    class SelfAttention_v1(nn.Module):
        def __init__(self, d_in, d_out):
            super().__init__()
            self.d_out = d_out
            # 手动初始化权重参数矩阵：W_query、W_key、W_value
            self.W_query = nn.Parameter(torch.rand(d_in, d_out))
            self.W_key   = nn.Parameter(torch.rand(d_in, d_out))
            self.W_value = nn.Parameter(torch.rand(d_in, d_out))

        def forward(self, x):
            # 计算权重向量：queries、keys、values
            keys = x @ self.W_key
            queries = x @ self.W_query
            values = x @ self.W_value
            # 计算注意力得分
            attn_scores = queries @ keys.T
            # 计算注意力权重
            attn_weights = torch.softmax(attn_scores / keys.shape[-1]**0.5, dim=-1)
            # 计算上下文向量
            context_vec = attn_weights @ values
            return context_vec
    print("实现一个简洁的自注意力机制V1类：")
    torch.manual_seed(123)
    sa_v1 = SelfAttention_v1(d_in, d_out)
    print(sa_v1(inputs))
    ```

  * 实现一个简洁的自注意力机制V2类：

    ```python
    class SelfAttention_v2(nn.Module):
        def __init__(self, d_in, d_out, qkv_bias=False):
            super().__init__()
            self.d_out = d_out
            # 自动初始化权重参数矩阵：W_query、W_key、W_value
            self.W_query = nn.Linear(d_in, d_out, bias=qkv_bias)
            self.W_key   = nn.Linear(d_in, d_out, bias=qkv_bias)
            self.W_value = nn.Linear(d_in, d_out, bias=qkv_bias)

        def forward(self, x):
            # 计算权重向量：queries、keys、values
            keys = self.W_key(x)
            queries = self.W_query(x)
            values = self.W_value(x)
            # 计算注意力得分
            attn_scores = queries @ keys.T
            # 计算注意力权重
            attn_weights = torch.softmax(
                attn_scores / keys.shape[-1]**0.5, dim=-1)
            # 计算上下文向量
            context_vec = attn_weights @ values
            return context_vec
    print("实现一个简洁的自注意力机制V2类：")
    torch.manual_seed(789)
    sa_v2 = SelfAttention_v2(d_in, d_out)
    print(sa_v2(inputs))
    ```

    ```v2```与```v1```的区别在于当禁用偏置单元时，```nn.Linear``` 层可以有效地执行矩阵乘法。此外，使用 ```nn.Linear``` 替代手动实现的 ```nn.Parameter(torch.rand(...))``` 的一个显著优势在于，```nn.Linear``` 具有优化的权重初始化方案，从而有助于实现更稳定和更高效的模型训练。

### 使用因果注意力机制来屏蔽后续词

* 因果注意力（也称为掩蔽注意力）是一种特殊的自注意力形式。它限制模型在处理任何给定的 ```token``` 时，只考虑当前以及之前 ```token```，而不能看到后续内容，因此需要对每个处理的 ```token``` 屏蔽其后续 ```token```。

* 对注意力权重的对角线上方部分进行了掩码操作，并对未掩码的注意力权重进行归一化，使得每一行的注意力权重之和为 1：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm31.png)

  ```python
  # 实现因果注意力掩码V1
  print("实现因果注意力掩码V1：")
  queries = sa_v2.W_query(inputs)
  print("当前q向量：")
  print(queries)
  keys = sa_v2.W_key(inputs)
  print("当前k向量：")
  print(keys)
  attn_scores = queries @ keys.T
  print("当前注意力得分：")
  print(attn_scores)
  attn_weights = torch.softmax(attn_scores / keys.shape[-1]**0.5, dim=-1)
  print("当前注意力权重：")
  print(attn_weights)
  # 生成对角线以下为1的掩码矩阵
  print("生成对角线以下为1的掩码矩阵：")
  context_length = attn_scores.shape[0]
  mask_simple = torch.tril(torch.ones(context_length, context_length))
  print(mask_simple)
  # 将当前注意力权重对角线以上的值置零
  print("将当前注意力权重对角线以上的值置零：")
  masked_simple = attn_weights*mask_simple
  print(masked_simple)
  # 重新归一计算注意力权重
  print("重新归一计算注意力权重：")
  row_sums = masked_simple.sum(dim=-1, keepdim=True)
  masked_simple_norm = masked_simple / row_sums
  print(masked_simple_norm)
  ```

  ```torch.ones```表示生成一个全为 1 的张量；```torch.tril```表示生成一个下三角矩阵，其中下三角矩阵的对角线以下的元素为 1（包含对角线），其余元素为 0。

  还可以利用 ```softmax``` 函数的数学特性（当一行中存在负无穷值（```-∞```）时，```Softmax``` 函数会将这些值视为零概率。），更高效地计算掩码后的注意力权重，减少计算步骤：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm32.png)

  ```python
  # 实现因果注意力掩码V2
  print("实现因果注意力掩码V2：")
  # 生成对角线以上为1（不包含对角线）的掩码矩阵
  print("生成对角线以上为1（不包含对角线）的掩码矩阵：")
  mask = torch.triu(torch.ones(context_length, context_length), diagonal=1)
  print(mask)
  attn_scores_masked = attn_scores.masked_fill(mask.bool(), -torch.inf) # 先将0-1掩码矩阵转换为false-true掩码矩阵，然后将注意力得分矩阵在遇到true的时候替换为-inf，false时保留原值
  print(attn_scores_masked)
  # 归一计算注意力权重
  print("归一计算注意力权重：")
  attn_weights_masked = torch.softmax(attn_scores_masked / keys.shape[-1]**0.5, dim=-1)
  print(attn_weights_masked)
  ```

  ```torch.triu```表示生成上三角矩阵，其中上三角矩阵的对角线以上元素为 1（```diagonal=1```，不包含对角线），其余元素为 0；```torch.bool```表示将掩码矩阵转换为布尔类型，布尔类型中0表示```false```，1表示```true```；```torch.masked_fill```表示将注意力得分矩阵在遇到```true```的时候替换为```-inf```，```false```时保留原值。

* 使用 ```dropout``` 遮掩额外的注意力权重防止过拟合，确保模型不会过于依赖任何特定的隐藏层单元组合，提高模型的泛化能力。需要注意的是，仅在训练过程中使用，训练结束后则会禁用：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm33.png)

  ```python
  # 应用dropout掩码，减少在训练时过拟合
  print("应用dropout掩码，减少在训练时过拟合：")
  dropout = torch.nn.Dropout(0.5) # 每个元素都有 50% 的概率被置为 0
  print(dropout(attn_weights_masked))
  ```
  
  当对注意力权重矩阵应用 50% 的 ```dropout``` 时，矩阵中一半的元素会被随机设置为零。为了补偿有效元素的减少，矩阵中剩余元素的值会被放大 ```1/0.5 = 2``` 倍，公式如下：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm34.png)

  缩放操作的作用：

    * 增大未遮盖值的相对差异：放大剩余权重后，它们的数值相对于被置零的权重增大，从而拉大了非零元素之间的相对差异。这使得在 ```Softmax``` 计算中（输入值的差异越大，输出分布就会越尖锐；而输入值差异越小，输出分布就会越平滑），剩下的值之间的对比更明显，从而影响 ```Softmax``` 输出的分布形态。
    * 增强模型的选择性关注：在训练中，模型会在每个步骤中随机选择不同的 ```token``` 进行更高的关注，这使模型在学习时不会依赖特定 ```token``` 的注意力。

### 从单头注意力扩展到多头注意力