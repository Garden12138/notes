## 处理文本数据

### 理解词嵌入

* 文本数据是离散的分类数据，它与实现和训练神经网络所需的数学运算的数据格式不兼容，故需要一种方法将数据转换为向量格式，这个过程称为嵌入```Embeding```。

* 可通过特定的神经网络层或其他预训练的神经网络模型对不同类型的数据进行嵌入，如视频、音频、文本：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm1.png)

  不同的数据格式需要使用不同的嵌入模型，原因在于它们的数据结构、特征和处理方式各不相同：

  |数据类型|数据特征|嵌入模型|主要特征|
  |:--:|:--|:--|:--|
  |文本|离散的、序列化的符号数据|Word2Vec、BERT、GPT等|语义关系、上下文理解|
  |图像|二维像素网格，具有空间特征|CNN（ResNet、VGG）、ViT|形状、纹理、颜色等视觉特征|
  |音频|一维时序信号|CNN+频谱图、RNN、Transformer|频率、音调、时序依赖|
  |视频|时空序列数据|3D CNN、RNN+CNN、Video Transformer|时空特征、动作捕捉|

* ```Word2Vec```是最受欢迎的生成单词嵌入框架，它通过预测给定目标词的上下文，训练神经网络架构以生成单词嵌入，核心思想是出现在相似上下文中的词通常具有相似的含义。因此，当将单词投影到二维空间进行可视化时，可以看到相似的词汇聚在一起：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm2.png)

  词嵌入可以具有不同的维度，从一维到数千维。上图选择二维词嵌入进行可视化，更高的维度可能捕捉到更细微的关系，如最小的```GPT-2```模型（```117M```和```125M```参数）使用 768 维的嵌入大小，而最大的```GPT-3```模型（```175B``参数）则使用 12,288 维的嵌入大小。通常，在性能与效率之间的权衡下，嵌入的大小（维度）会根据具体的模型变体和大小而有所不同。

* 虽然可使用预训练模型（如```Word2Vec```）为机器学习模型生成嵌入，但```LLM```通常会生成自己的嵌入，这些嵌入是输入层的一部分，并在训练过程中进行更新。将嵌入作为```LLM```训练的一部分进行优化，而不直接使用```Word2Vec```，有一个明确的优势，就是嵌入能够针对特定的任务和数据进行优化。

* ```Word2Vec```是单词嵌入，是最常用的文本嵌入形式，同时还存在句子、段落或整篇文档的嵌入，这种嵌入常被用于检索增强生成技术（```RAG```），它将外部知识库（如文档、数据库、互联网等）进行向量化后存入到向量数据库中。当用户提交一个查询时，首先将这个查询也编码成一个向量，然后去承载外部知识库的向量数据库中检索（检索技术有很多种）与问题相关的信息，检索到的信息被作为额外的上下文信息输入到```LLM```中，```LLM```会将这些外部信息与原始输入结合起来，以更准确和丰富的内容生成回答，解决大模型存在的知识时效性、模型大小限制知识范围以及生成内容出现幻觉现象等问题。

### 文本分词

* 输入文本到创建嵌入向量的第一步是文本分词，将长文本分割成单个单词或特殊字符，包括标点符号，分割后的单位称为```token```：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm3.png)

* 我们使用正则表达式进行文本分词，但在第一步我们应该是获取输入文本：

  ```python
  with open("the-verdict.txt", "r", encoding="utf-8") as f:
          raw_text = f.read()
  print("Total number of character:", len(raw_text))
  print(raw_text[:99])
  ```

  其中```the-verdict.txt```是一部由[```Edith Wharton```创作的短篇小说《判决》](https://en.wikisource.org/wiki/The_Verdict)，我们可以点击下载到本地。

  下一步，我们使用正则表达式，用空格、标点符号、换行符等进行分割，并且对分割结果进行去除空字符串的操作（去除操作按需进行）：

  ```python
  preprocessed = re.split(r'([,.:;?_!"()\']|--|\s)', raw_text)
  preprocessed = [item.strip() for item in preprocessed if item.strip()]
  print(len(preprocessed))
  ```

### 将 tokens 转换为 token IDs

* 在文本分词之后，我们需要将生成的```token```从字符串转换为整形以创建```token ID```，这个转换过程依赖预先定义的词汇表：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm4.png)

* 定义词汇表：

  ```python
  all_tokens = sorted(set(preprocessed))
  vocab = {token:integer for integer,token in enumerate(all_tokens)}
  ```

* 创建分词器：

  ```python
  class SimpleTokenizerV1:
        def __init__(self, vocab):
            self.str_to_int = vocab                                                   
            self.int_to_str = {i:s for s,i in vocab.items()}                          

      def encode(self, text):                                                       
            preprocessed = re.split(r'([,.?_!"()\']|--|\s)', text)
            preprocessed = [item.strip() for item in preprocessed if item.strip()]
            ids = [self.str_to_int[s] for s in preprocessed]
            return ids

      def decode(self, ids):                                                        
            text = " ".join([self.int_to_str[i] for i in ids])
            text = re.sub(r'\s+([,.?!"()\'])', r'\1', text) # 去掉标点符号前面多余的空格："Hello , world !" -> "Hello, world!"                         
            return text
  ```

  ```str_to_int```维护词汇表，用于```encode```方法中，将```token```转换为```token ID```；```int_to_str```维护反词汇表，用于```decode```方法中，将```token ID```转换为```token```：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm5.png)

* 实例化分词器，对艾迪丝·华顿的短篇小说中的一段文本进行分词：

  ```python
  tokenizer = SimpleTokenizerV1(vocab)
  text = """"It's the last he painted, you know," Mrs. Gisburn said with pardonable pride."""
  ids = tokenizer.encode(text)
  print(ids)
  ```

  根据```token ID```找回文本：

  ```python
  raw_text = tokenizer.decode(ids)
  print(raw_text)
  ```     

  若使用文本```"Hello, do you like tea?"```，则会报错，因为词汇表不存在```Hello```：

  ```bash
  KeyError: 'Hello'
  ```

  这需要我们在分词过程中对于未知词汇应当有额外特殊处理。

### 添加特殊上下文token

* 未了解决未知词汇不在单词表导致无法将```Token```转为```Token ID```的问题，可添加特殊的上下文```Token```，如```<|unk|>```代表未知词汇，还加入```<|endoftext|>```代表文档结束位置，一般用于文档之间，这样可以让大模型更好的理解上下文：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm6.png)

* 修改词汇表，加入特殊上下文```Token```：

  ```python
  all_tokens = sorted(list(set(preprocessed)))
  all_tokens.extend(["<|endoftext|>", "<|unk|>"])
  vocab = {token:integer for integer,token in enumerate(all_tokens)}
  ```

* 修改分词器，当出现未知词汇时，使用特殊上下文```Token <|unk|>```代替：

  ```python
  class SimpleTokenizerV2:
        def __init__(self, vocab):
            self.str_to_int = vocab                                                   
            self.int_to_str = {i:s for s,i in vocab.items()}                          

      def encode(self, text):                                                       
            preprocessed = re.split(r'([,.?_!"()\']|--|\s)', text)
            preprocessed = [item.strip() for item in preprocessed if item.strip()]
            preprocessed = [item if item in self.str_to_int else "<|unk|>" for item in preprocessed]
            ids = [self.str_to_int[s] for s in preprocessed]
            return ids

      def decode(self, ids):                                                        
            text = " ".join([self.int_to_str[i] for i in ids])
            text = re.sub(r'\s+([,.?!"()\'])', r'\1', text) # 去掉标点符号前面多余的空格："Hello , world !" -> "Hello, world!"                         
            return text
  ```

* 实例化分词器，使用两个用特殊上下文```Token```（如```<|endoftext|>```）连接的文本：

  ```python
  text1 = "Hello, do you like tea?"
  text2 = "In the sunlit terraces of the palace."
  text = " <|endoftext|> ".join((text1, text2))
  tokenizer = SimpleTokenizerV2(vocab)
  ids = tokenizer.encode(text)
  print(ids)
  ```

  根据```token ID```找回文本：

  ```python
  raw_text = tokenizer.decode(ids)
  print(raw_text)
  ```  

* 实际应用我们并不会用此方法，对于```|<unk>|```，一般使用```BPE```算法代替，对于```|<endoftext>|```，一般使用掩码矩阵来代替：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm7.png)

  在训练神经网络时，通常会将不同长度的句子或文本批处理为一个```batch```进行并行训练，这时需要将不同长度的句子齐到同一长度（基于矩阵运算要求形状一致），这时就需要填充特殊上下文```Token```（如```<|endoftext|>```） 来对齐所有序列的长度，使得模型能够有效处理不同长度的输入。但我们使用掩码矩阵，用掩码标识哪个```Token```是有效的，哪个是```Token```是无效的，无需填充特殊上下文```Token```。

### 字节对编码（Byte Pair Encoding，BPE）

* 从上述的按分割线符号进行文本分词，将分词结果```token```转换为```token ID```，其中在转换过程中添加特殊上下文```token```以达到处理未知词汇的目的，但这种方法存在问题，如分词没有语义概念，很多未知词汇共用一个```token ID```，用于训练模型意义不大，我们将使用曾用于训练大语言模型，如```GPT-2```、```GPT-3```以及最初用于```ChatGPT```的```LLM```的```BPE```分词器进行分词。

* ```BPE```（```Byte Pair Encoding```字节对编码）是一种基于统计的方法，它会先从整个语料库中找出最常见的字节对（```byte pair```），然后把这些字节对合并成一个新的单元。对于这个算法的理解可参考[这篇文章](../../BPE%20algorithm%20analysis.md)：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm8.png)

* 使用```BPE```分词器：

  * 安装```tiktoken```库：

    ```bash
    pip install tiktoken
    ```

  * 实例化分词器：

    ```python
    import tiktoken

    tokenizer = tiktoken.get_encoding("gpt2")
    ```

  * 分词编码：

    ```python
    text = "Hello, do you like tea? <|endoftext|> In the sunlit terraces of someunknownPlace."
    integers = tokenizer.encode(text, allowed_special={"<|endoftext|>"})
    print(integers)
    ```

  * 分词解码：

    ```python
    strings = tokenizer.decode(integers)
    print(strings)
    ```

### 使用滑动窗口进行数据采样

* 在使用```BPE```分词后，我们成功将文本转换为```Token IDS```，接下来我们要为```Token IDS```之间构建关系"输入（块）-目标（预测的下一个词） 对"：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm9.png)

  通过代码了解"输入-目标对"，首先准备数据，创建变量```x```和```y```：

  ```python
  # 分词
  with open("the-verdict.txt", "r", encoding="utf-8") as f:
      raw_text = f.read()
      enc_text = tokenizer.encode(raw_text)
  # 移除前50个token，以方便演示
  enc_sample = enc_text[50:]
  # 创建变量x和y
  context_size = 4                    #A
  x = enc_sample[:context_size]
  y = enc_sample[1:context_size+1]
  print(f"x: {x}")
  print(f"y:    {y}")
  ``` 
  
  输出：

  ```bash
  x: [290, 4920, 2241, 287]
  y:       [4920, 2241, 287, 257]
  ```

  构建"输入-目标对"：

  ```python
  for i in range(1, context_size+1):
  context = enc_sample[:i]
  desired = enc_sample[i]
  print(context, "---->", desired)
  ```

  输出：

  ```bash
  [290] ----> 4920
  [290, 4920] ----> 2241
  [290, 4920, 2241] ----> 287
  [290, 4920, 2241, 287] ----> 257
  ```

* 构建张量```x```和```y```数据集：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm10.png)

  张量```x```中的每一行代表一个输入上下文，对应着张量```y```中的每一行预测目标，按照上述例子说明，这两行数据就可以生成4行```（max_length```）"输入-目标对"。张量```x```的第二行代表使用滑动窗口进行1步（```stride```）移动后的输入上下文，但这容易导致这两批次之间出现重叠，过多的重叠可能会导致过拟合。代码实现如下：

  ```python
  import torch
  from torch.utils.data import Dataset, DataLoader

  class GPTDatasetV1(Dataset):
      def __init__(self, txt, tokenizer, max_length, stride):
          self.input_ids = [] # 张量x
          self.target_ids = [] # 张量y
          #A 将整个文本进行分词
          token_ids = tokenizer.encode(txt)                                
          # 使用滑动窗口将书籍分块为最大长度的重叠序列
          # 以stride为步长，从文本头开始切长度为max_length的覆盖窗口，一直切到不能再切完整窗口为止，否则会越界
          # 因为chunk是：[i : i + max_length]
          # 所以i最大只能是：len(token_ids) - max_length
          for i in range(0, len(token_ids) - max_length, stride):          
              input_chunk = token_ids[i:i + max_length] # 张量x的一行
              target_chunk = token_ids[i + 1: i + max_length + 1] # 张量y的一行
              self.input_ids.append(torch.tensor(input_chunk))
              self.target_ids.append(torch.tensor(target_chunk))

      # 返回数据集的总行数
      def __len__(self):                                                     
          return len(self.input_ids)
          
      # 从数据集中返回指定行
      def __getitem__(self, idx):                                            
          return self.input_ids[idx], self.target_ids[idx]
  ```

* 实现数据加载器：

  ```python
  def create_dataloader_v1(txt, batch_size=4, max_length=256,
                         stride=128, shuffle=True, drop_last=True, num_workers=0):
      # 初始化分词器
      tokenizer = tiktoken.get_encoding("gpt2")
      # 创建张量x和y数据集                       
      dataset = GPTDatasetV1(txt, tokenizer, max_length, stride)
      # 创建数据加载器
      dataloader = DataLoader(
          dataset,
          batch_size=batch_size,
          shuffle=shuffle,
          drop_last=drop_last,                                
          num_workers=0                                       
      )
  return dataloader
  ```

  参数```txt```为文本内容，```batch_size```为每次加载的样本数（即从张量x和y中取出多少行数据），```max_length```为输入序列的最大长度，```stride```为滑动窗口的步长，```shuffle```为是否打乱数据集顺序，```drop_last```为是否丢弃最后一个不完整的样本，```num_workers```为加载数据时的进程数。使用数据加载器：

  ```python
  with open("the-verdict.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()

  dataloader = create_dataloader_v1(
      raw_text, batch_size=1, max_length=4, stride=1, shuffle=False)
  # 将数据加载器转换为Python迭代器，通过next()函数获取下一批数据。
  data_iter = iter(dataloader)
  first_batch = next(data_iter)
  print(first_batch)
  ```

  输出：
  
  ```bash
  [tensor([[ 40, 367, 2885, 1464]]), tensor([[ 367, 2885, 1464, 1807]])]
  ```

  ```first_batch```变量包含两个张量：第一个张量存储输入```token ID```，第二个张量存储目标```token ID```。由于```max_length```设置为4，因此这两个张量各包含4个```token ID```。

  继续获取第二批数据，可看出```stride=1```的含义：

  ```python
  second_batch = next(data_iter)
  print(second_batch)
  ```

  输出：

  ```bash
  [tensor([[ 367, 2885, 1464, 1807]]), tensor([[2885, 1464, 1807, 3619]])]
  ```

  将第一个批次与第二个批次进行比较，可以看到第二个批次的```token ID```相较于第一个批次右移了一个位置（例如，第一个批次输入中的第二个```ID``` 是367，而它是第二个批次输入的第一个```ID```）。若想分别输出```Input```和```Target```，可：

  ```python
  inputs, targets = next(data_iter)
  print("Inputs:\n", inputs)
  print("\nTargets:\n", targets)
  ```

### 构建词嵌入层

* 在准备好张量```x```和```y```数据集以及对应数据加载器后，我们可以构建词嵌入层，将```token ID```转换为嵌入向量，这是为```LLM```准备训练集的最后一步：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm11.png)

  嵌入向量这种连续向量的表示方式，对于```GPT```类的大语音模型是非常重要的：

    * 这类模型使用的深度神经网络结构只能对数值数据进行有效计算，离散文字数据（如单词、句子）是无法处理的，而连续向量可在高维空间中表示文本的语义关系，适用于神经网络的计算。

    * 深度神经网络通过反向传播算法进行训练，反向传播的本质是利用梯度下降法来更新网络的权重，以最小化损失函数（```loss function```）。反向传播要求每一层的输入、输出和权重都能够参与梯度计算、更新，要求输入的数据为数值（即向量）。关于反向传播算法可参考[这里]()。

* 实现嵌入向量层：

  * 创建权重矩阵：

    ```python
    # 假设词汇表大小为6，嵌入向量维度为3
    vocab_size = 6
    output_dim = 3
    # 随机种子设置123
    torch.manual_seed(123)
    # 创建权重矩阵
    embedding_layer = torch.nn.Embedding(vocab_size, output_dim)
    print(embedding_layer.weight)
    ```

    输出：

    ```bash
    Parameter containing:
    tensor([[ 0.3374, -0.1778, -0.1690],
                 [ 0.9178, 1.5810, 1.3010],
                 [ 1.2753, -0.2010, -0.1606],
                 [-0.4015, 0.9666, -1.1481],
                 [-1.1589, 0.3255, -0.6315],
                 [-2.8400, -0.7849, -1.4096]], requires_grad=True)
    ```

    从输出结果我们可以看出，3个数组元素代表1个```token ID```，并且```token ID```实际上为数组索引（本质上```token ID```是词表中的索引，而我们使用了词表的大小构建了权重矩阵），如```[ 0.3374, -0.1778, -0.1690]```代表```token ID=0```的嵌入向量。

  * 实现嵌入矩阵：

    ```python
    input_ids = torch.tensor([2, 3, 5, 1])

    print(embedding_layer(input_ids))
    ```

    输出：

    ```bash
    tensor([[ 1.2753, -0.2010, -0.1606],     # token ID=2
                [-0.4015, 0.9666, -1.1481],  # token ID=3
                [-2.8400, -0.7849, -1.4096], # token ID=5
                [ 0.9178, 1.5810, 1.3010]],  # token ID=1
                grad_fn=<EmbeddingBackward0>)
    ``` 

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm12.png)

### 位置编码