## 集成 Minio

> 引入依赖：

```bash
<properties>
    <minio.version>8.5.6</minio.version>
</properties>

<dependency>
    <groupId>io.minio</groupId>
    <artifactId>minio</artifactId>
    <version>${minio.version}</version>
</dependency>
```

> 配置文件 application.yaml 添加 Minio 配置：

```bash
minio:
  endpoint: ${MINIO_SERVER_API_ADDRESS} # 设置minio服务端api访问地址
  bucketName: minio-client # 指定桶
  accessKey: 5YuRY1kvChIgQolh8NnJ # 设置访问key
  secretKey: o1t7nv7GEcVywwRsB8oLItCKMWuWYeMNDr0BTKZO # 设置密钥
```

> 新增配置类 MinioConfig 初始化 minioClient Bean：

```bash
@Data
@Configuration
@ConfigurationProperties(prefix = "minio")
public class MinioConfig {

    private String endpoint;
    private String bucketName;
    private String accessKey;
    private String secretKey;

    @Bean
    public MinioClient minioClient() {
        return MinioClient.builder()
                .endpoint(endpoint)
                .credentials(accessKey, secretKey)
                .build();
    }

}
```

> 新增服务类 MinioService，封装 minio client 常用 api：

```bash
@Slf4j
@Service
public class MinioService {

    @Autowired
    private MinioClient minioClient;

    @Autowired
    private MinioConfig minioConfig;


    /**
     * 查看bucket是否存在
     *
     * @param bucketName
     * @return
     */
    public boolean bucketExists(String bucketName) {
        try {
            boolean result = minioClient.bucketExists(BucketExistsArgs.builder()
                    .bucket(bucketName)
                    .build());
            return result;
        } catch (Exception e) {
            log.error("bucketExists error, msg: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 上传文件
     *
     * @param multipartFile
     * @return
     */
    public boolean uploadFile(MultipartFile multipartFile) {
        try {
            InputStream inputStream = multipartFile.getInputStream();
            minioClient.putObject(PutObjectArgs.builder()
                    .bucket(minioConfig.getBucketName())
                    .object(multipartFile.getOriginalFilename())
                    .stream(inputStream, multipartFile.getSize(), -1)
                    .contentType(multipartFile.getContentType())
                    .build());
            return true;
        } catch (Exception e) {
            log.error("uploadFile error, msg: {}", e.getMessage());
            return false;
        }
    }


    /**
     * 下载文件
     *
     * @param fileName
     * @param request
     * @param response
     * @return
     */
    public void downloadFile(String fileName, HttpServletRequest request, HttpServletResponse response) {
        try {
            response.setCharacterEncoding("UTF-8");
            ServletOutputStream os = response.getOutputStream();
            GetObjectResponse is = minioClient.getObject(GetObjectArgs.builder()
                    .bucket(minioConfig.getBucketName())
                    .object(fileName)
                    .build());
            response.setHeader("Content-Disposition", "attachment;filename=" + DownLoadUtil.getFileName(request.getHeader("user-agent"), fileName));
            ByteStreams.copy(is, os);
            os.flush();
        } catch (Exception e) {
            log.error("downloadFile error, msg: {}", e.getMessage());
        }

    }

    /**
     * 删除文件
     *
     * @param fileName
     * @return
     */
    public boolean removeFile(String fileName) {
        try {
            minioClient.removeObject(RemoveObjectArgs.builder()
                    .bucket(minioConfig.getBucketName())
                    .object(fileName)
                    .build());
            return true;
        } catch (Exception e) {
            log.error("removeFile error, msg: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 获取文件Url
     *
     * @param fileName
     * @return
     */
    public String getFileUrl(String fileName) {
        try {
            return minioClient.getPresignedObjectUrl(GetPresignedObjectUrlArgs.builder()
                    .bucket(minioConfig.getBucketName())
                    .object(fileName)
                    .method(Method.GET)
                    .build());
        } catch (Exception e) {
            log.error("getFileUrl error, msg: {}", e.getMessage());
            return "";
        }
    }

    /**
     * 查看文件对象
     *
     * @param fileName
     * @return
     */
    public FileObject getFileObject(String fileName) {
        FileObject fileObject = new FileObject();
        try {
            GetObjectResponse result = minioClient.getObject(GetObjectArgs.builder()
                    .bucket(minioConfig.getBucketName())
                    .object(fileName)
                    .build());
            fileObject.setBucket(result.bucket());
            fileObject.setRegion(result.region());
            fileObject.setObject(result.object());
        } catch (Exception e) {
            log.error("getFileObject error, msg: {}", e.getMessage());
        }
        return fileObject;
    }

}
```

> [完整代码](https://gitee.com/FSDGarden/minio-client)

> 注意事项

* 上述的```accessKey```以及```secretKey```在```minio-server```中配置：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minio/Snipaste_2023-10-26_17-16-37.png)

* ```minio-server```的简单概念介绍以及基础使用可参考[这里](https://juejin.cn/post/7206973995727372343)。

* ```MinioService```服务类对于```minio api```的封装可参考[这里](https://github.com/zhengjiaao/spring-boot-starter-minio/tree/master)。

> 参考文献

* [Springboot集成Minio](https://juejin.cn/post/7209110611858309179)