## 博今智推商户端
http://8.134.39.135		
100027/15818468674/bj_15818468674
100058/15818468674/bj_15818468674
100075/13533778548/bj_13533778548
## 博今智推运营端
http://8.134.39.135:81
admin/Bj@123456	ceshi/812458
## mysql（博今智推-测试）：
地址：8.134.39.135:13306/bjzt_cloud
账号：bjzt_cloud
密码：7BWnz3EMhWGjAdhJ
## 测试环境
8.134.39.135:22
root
Hyzh2021@!!
文件目录：/mnt/bjzt/bjzt-cloud/
## nacos
http://8.134.39.135:18848/nacos/
nacos
bojinNacos20221014
## 项目缺陷管理
http://zentao.bojin-tech.com/
密码：Bojinit2022
## vm options
-Dspring.cloud.nacos.discovery.group=zjd
## 阿里云oss
// Endpoint以华东1（杭州）为例，其它Region请按实际情况填写。
String endpoint = "https://oss-cn-hangzhou.aliyuncs.com";
// 阿里云账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM用户进行API访问或日常运维，请登录RAM控制台创建RAM用户。
String accessKeyId = "LTAI5tFSUVkf5X6DfKt3EzDG";
String accessKeySecret = "LznZdFGTbTRrFTge0eB1mfK3MfjE4E";
// 填写Bucket名称，例如examplebucket。
String bucketName = "bjzt-oss";
// 填写Object完整路径，完整路径中不能包含Bucket名称，例如exampledir/exampleobject.txt。
String objectName = "bj-shop/exampleobject.txt";

## todo list
1.封装根据人群包ID获取客户信息API（现阶段取手机号码）✅
2.同步人群包接口：根据人群包ID获取客户手机号码信息->自动批量保存人群包信息（包含撞库功能、指定用户功能(tenant_id)）✅
```
## nacos配置上 zt.sync.crowdpkg.trumpchi.open: 0 时，支持传参数tenantCode，tenantUserName，request body:
{
    "tenantCode":100033,
    "tenantUserName":"13588888888",
    "syncPkgId":"63291fe5e4b073452102b1ad",
    "syncPkgName":"测试1",
    "pageNumber":1,
    "pageSize":1000
}
```
```
## 增量SQL
ALTER TABLE crowd_pkg ADD sync_pkg_id VARCHAR(64) COMMENT '同步人群包ID';
```
```
# Nacos 测试环境新增配置
cdp.username: 13533778548
cdp.app.key: 3dd513d4-2952-4682-bd4d-7523e8d2035d
zt.sync.crowdpkg.trumpchi.open: 1
zt.sync.crowdpkg.trumpchi.tenantCode: 100027
zt.sync.crowdpkg.trumpchi.tenantUserName: 15818468674

# Nacos 生产环境新增配置
cdp.username: 13533778548
cdp.app.key: 3dd513d4-2952-4682-bd4d-7523e8d2035d
zt.sync.crowdpkg.trumpchi.open: 1
zt.sync.crowdpkg.trumpchi.tenantCode: 100019
zt.sync.crowdpkg.trumpchi.tenantUserName: 13048554389
```
3.获取人群包列表接口 ✅
4.根据人群包id获取客户信息接口 ✅
5.根据人群包id获取客户电话接口 ✅

1.新增沉淀CDP人群包列表信息接口
```
CREATE TABLE `cdp_crowd_pkg` (
  `id` bigint(20) NOT NULL COMMENT '主键',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime DEFAULT NULL COMMENT '修改时间',
  `create_user_id` bigint(20) DEFAULT NULL COMMENT '创建人id',
  `create_user_name` varchar(255) DEFAULT NULL COMMENT '创建人',
  `update_user_id` bigint(20) DEFAULT NULL COMMENT '更新人id',
  `update_user_name` varchar(255) DEFAULT NULL COMMENT '更新人',
  `crowd_id` varchar(64) DEFAULT NULL COMMENT '人群包id',
  `version_time_latest` varchar(20) DEFAULT NULL COMMENT '人群包最新版本',
  `crowd_name` varchar(64) DEFAULT NULL COMMENT '人群包名称',
  `remarks` varchar(64) DEFAULT NULL COMMENT '人群包备注信息',
  `user_count` int(10) DEFAULT NULL COMMENT '人群包中的人数',
  `update_type` varchar(64) DEFAULT NULL COMMENT '更新方式',
  `update_frequency` varchar(64) DEFAULT NULL COMMENT '更新周期',
  `is_sync` int(2) DEFAULT '0' COMMENT '是否已同步，0为否，1为是',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `crowd_id_idx` (`crowd_id`) USING BTREE,
  KEY `crowd_name_idx` (`crowd_name`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COMMENT='CDP人群包表';
```
2.新增获取未同步人群包信息分页列表接口 ✅
3.新增批量同步人群包接口 ✅
4.修改人群包分页列表接口-新增数据来源，默认为系统，有同步人群包id为同步 ✅

1.新增传祺-获取标签维度列表接口 ✅
2.封装根据标签ID列表获取客户信息API（现阶段取手机号码）✅
3.新增沉淀标签信息列接口 ✅
```
CREATE TABLE `cdp_label_category` (
  `id` bigint(20) NOT NULL COMMENT '主键',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime DEFAULT NULL COMMENT '修改时间',
  `create_user_id` bigint(20) DEFAULT NULL COMMENT '创建人id',
  `create_user_name` varchar(255) DEFAULT NULL COMMENT '创建人',
  `update_user_id` bigint(20) DEFAULT NULL COMMENT '更新人id',
  `update_user_name` varchar(255) DEFAULT NULL COMMENT '更新人',
  `label_category_id` varchar(64) DEFAULT NULL COMMENT '标签目录id',
  `label_category_name` varchar(64) DEFAULT NULL COMMENT '标签目录名称',
  `pid` bigint(20) DEFAULT NULL COMMENT '父级id',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `label_category_id_idx` (`label_category_id`) USING BTREE,
  KEY `label_category_name_idx` (`label_category_name`) USING BTREE,
  KEY `pid_idx` (`pid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COMMENT='CDP标签目录表';

CREATE TABLE `cdp_label_detail` (
  `id` bigint(20) NOT NULL COMMENT '主键',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime DEFAULT NULL COMMENT '修改时间',
  `create_user_id` bigint(20) DEFAULT NULL COMMENT '创建人id',
  `create_user_name` varchar(255) DEFAULT NULL COMMENT '创建人',
  `update_user_id` bigint(20) DEFAULT NULL COMMENT '更新人id',
  `update_user_name` varchar(255) DEFAULT NULL COMMENT '更新人',
  `label_update_time` varchar(32) DEFAULT NULL COMMENT '标签更新时间',
  `label_id` varchar(64) DEFAULT NULL COMMENT '标签id',
  `label_describe` varchar(256) DEFAULT NULL COMMENT '标签描述',
  `label_name` varchar(64) DEFAULT NULL COMMENT '标签名称',
  `cdp_label_category_id` bigint(20) DEFAULT NULL COMMENT '标签目录表id',
  `pre_label_category_id` varchar(64) DEFAULT NULL COMMENT '上一级标签目录id',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `label_update_time_idx` (`label_update_time`) USING BTREE,
  KEY `label_id_idx` (`label_id`) USING BTREE,
  KEY `label_name_idx` (`label_name`) USING BTREE,
  KEY `cdp_label_category_id_idx` (`cdp_label_category_id`) USING BTREE,
  KEY `pre_label_category_id_idx` (`pre_label_category_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COMMENT='CDP标签明细表';
```
4.新增获取标签信息列表接口 ✅
5.保存所选标签信息接口：根据所选标签获取客户手机号码信息->自动批量保存人群包信息（包含撞库功能）-> 建立手机号码与维度标签关联关系 ✅
```
CREATE TABLE `cdp_label_mobile_rel` (
  `id` bigint(20) NOT NULL COMMENT '主键',
  `label_id` varchar(64) DEFAULT NULL COMMENT '标签id',
  `mobile` varchar(20) DEFAULT NULL COMMENT '手机号码',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `label_id_idx` (`label_id`) USING BTREE,
  KEY `mobile_idx` (`mobile`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COMMENT='CDP标签与手机号码关联表';
```

1.新增同步标签维度信息接口（新增标签维度表）-- 暂时不做
2.同步人群包逻辑新增手机号码关联标签维度的功能（新增手机号码与标签关联表）-- 暂时不做

标签模块流程：
1.维护客户、商品、会员标签 ✅
```
CREATE TABLE `crm_label_type` (
  `id` bigint(20) NOT NULL COMMENT 'ID主键',
  `type_name` varchar(64) NOT NULL COMMENT '类型名称',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `parent_id` bigint(20) DEFAULT NULL COMMENT '上一级类型ID',
  `model` int(2) NOT NULL COMMENT '所属模块，0为客户，1为商品，2为会员',
  `sort` int(11) DEFAULT NULL COMMENT '排序',
  `is_delete` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除(true-删除;false-未删除)',
  `enabled` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否启用(true-启用;false-禁用)',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime DEFAULT NULL COMMENT '修改时间',
  `create_user_id` bigint(20) DEFAULT NULL COMMENT '创建人id',
  `create_user_name` varchar(255) DEFAULT NULL COMMENT '创建人',
  `update_user_id` bigint(20) DEFAULT NULL COMMENT '更新人id',
  `update_user_name` varchar(255) DEFAULT NULL COMMENT '更新人',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `type_name_idx` (`type_name`) USING BTREE,
  KEY `parent_id_idx` (`parent_id`) USING BTREE,
  KEY `model_idx` (`model`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COMMENT='标签类型表';
```
```
CREATE TABLE `crm_label` (
  `id` bigint(20) NOT NULL COMMENT 'ID主键',
  `label_name` varchar(64) NOT NULL COMMENT '标签名称',
  `source_from` varchar(128) DEFAULT NULL COMMENT '标签数据来源',
  `parent_id` bigint(20) DEFAULT NULL COMMENT '上一级标签ID',
  `label_type_id` bigint(20) NOT NULL COMMENT '标签类型ID',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `sort` int(11) DEFAULT NULL COMMENT '排序',
  `is_delete` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除(true-删除;false-未删除)',
  `enabled` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否启用(true-启用;false-禁用)',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime DEFAULT NULL COMMENT '修改时间',
  `create_user_id` bigint(20) DEFAULT NULL COMMENT '创建人id',
  `create_user_name` varchar(255) DEFAULT NULL COMMENT '创建人',
  `update_user_id` bigint(20) DEFAULT NULL COMMENT '更新人id',
  `update_user_name` varchar(255) DEFAULT NULL COMMENT '更新人',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `label_name_idx` (`label_name`) USING BTREE,
  KEY `parent_id_idx` (`parent_id`) USING BTREE,
  KEY `label_type_id_idx` (`label_type_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COMMENT='标签表';
```

2.客户、商品、会员模块绑定标签 刘进负责

3.新增人群圈选包标签回显接口 ✅
```
# Nacos 测试环境新增配置
crm.base.label.typeIds: 1028625649395814400,1028625649496477728
crm.buss.label.typeIds: 1028625649504866323
crm.virtual.static.customer.labelId: ad1aebb64cef274ea2fa248d8c580af6fb1d
crm.virtual.static.goods.labelId: 8d8f7a12f56c4d42669819f176d620da1464
crm.virtual.static.member.labelId: a708e809d257e54e68d8e3c53b24a563eb5a
crm.virtual.dynamic.customer.labelId: 29ad47a9f95efb4dac3bc5031ef1356f3fdc
crm.virtual.dynamic.goods.labelId: 990adf31487d9c4c8ee91ad253fbcc8693f3
crm.virtual.dynamic.member.labelId: c57b56f8b6e11647195b13dde180ade02b87

# Nacos 生产环境新增配置
# 待定
crm.base.label.typeIds:
crm.buss.label.typeIds:
crm.virtual.static.customer.labelId: ad1aebb64cef274ea2fa248d8c580af6fb1d
crm.virtual.static.goods.labelId: 8d8f7a12f56c4d42669819f176d620da1464
crm.virtual.static.member.labelId: a708e809d257e54e68d8e3c53b24a563eb5a
crm.virtual.dynamic.customer.labelId: 29ad47a9f95efb4dac3bc5031ef1356f3fdc
crm.virtual.dynamic.goods.labelId: 990adf31487d9c4c8ee91ad253fbcc8693f3
crm.virtual.dynamic.member.labelId: c57b56f8b6e11647195b13dde180ade02b87
```

4.新增人群圈选包提交接口（包含动态SQL生成人群包功能）✅
5.动态可配置标签
5.0 新建动态标签分组接口 ✅
  - 标签分组对象新增是否可配置字段、是否支持最近天数搜索字段
    ```
    ALTER TABLE crm_label_type ADD config_flag tinyint(3) DEFAULT '0' COMMENT '是否可配置，0为不可配置，1为可配置，默认不可配置';
    ALTER TABLE crm_label_type ADD recent_days_search_flag tinyint(3) DEFAULT '0' COMMENT '是否支持最近天数搜索，0为不支持，1为支持，默认不支持';
    ALTER TABLE crm_label ADD `recent_days` int(11) DEFAULT '0' COMMENT '最近天数（动态可配置标签属性）';
    ```
5.1 新建动态标签接口 ✅
  - 支持设置所选标签分组的是否可配置、是否支持最近天数搜索字段值
5.2 获取Tab页标签接口 ✅
  - 新增返回动态可配置标签字段（返回的标签分组对象新增调用业务列表api的字段、返回业务列表字段名的字段，nacos内置）
```
# crm可动态标签配置信息
crm:
  dynlabel:
    config:
      infos:
        - typeName: 商品相关
          requestMethod: POST
          requestAddr: /crm/product/crmproduct/page
          idsConf: product_id
          timeConf: recent_days
          fields:
            - name: id
              value: 商品ID
            - name: introduction
              value: 商品名称
            - name: productImages
              value: 商品图片
            - name: cost
              value: 商品价格
        - typeName: 广告营销相关
          requestMethod: POST
          requestAddr: /ad/adInfo/list
          idsConf: ad_id
          fields:
            - name: id
              value: 广告ID
            - name: adName
              value: 广告名称
            - name: znsmsTemplateId
              value: 超信安卓版模板ID 
            - name: znsmsTemplateName
              value: 超信安卓版模板名称 
            - name: spsmsTemplateId
              value: 超信通用版模板ID
            - name: spsmsTemplateName
              value: 超信通用版模板名称
```
5.3 提交标签接口
  - 标签项对象新增所选表单字段值集合字段、业务列表字段名字段
  - 构建人群方式新增支持构建Where查询条件的方式
5.4 商品列表接口（/crm/product/crmproduct/page -> id、introduction、productImages、cost）、POST、product_id、recent_days ✅
5.5 广告列表接口（/ad/adInfo/list -> id、adName、znsmsTemplateId、znsmsTemplateName、spsmsTemplateId、spsmsTemplateName）、POST、 ad_id ✅

## 获取指定人群包手机号码
```
public static void main(String[] args) throws Exception {
    TrumpchiService service = new TrumpchiService();
    for (int i = 1; i <= 1; i++) {
        Thread.sleep(1000);
        FileWriter writer;
        writer = new FileWriter("/Users/cengjiada/Desktop/632c07ebe4b055c79a658629-第" + i + "页.txt");
        String phones = service.getCustomerPhoneList(i, 10000, "632c07ebe4b055c79a658629", null).
                    stream().collect(Collectors.joining(","));
        writer.write(phones);
        writer.flush();
        writer.close();
    }
}
```
```
TrumpchiService service = new TrumpchiService();
System.err.println(service.getCdpToken());
System.err.println(RSAUtil.decryptByPrivateKey(""));
```

```
docker run \
        --name=redis \
        --network=think_think\
        --hostname=3f4a29886c7e \
        --mac-address=02:42:ac:11:00:02 \
        --env=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        --env=GOSU_VERSION=1.12 \
        --env=REDIS_VERSION=5.0.14 \
        --env=REDIS_DOWNLOAD_URL=http://download.redis.io/releases/redis-5.0.14.tar.gz \
        --env=REDIS_DOWNLOAD_SHA=3ea5024766d983249e80d4aa9457c897a9f079957d0fb1f35682df233f997f32 \
        --volume=/etc/localtime:/etc/localtime:ro \
        --volume=/data \
        --workdir=/data \
        -p 6379:6379 \
        --restart=always \
        --runtime=runc \
        --detach=true \
        redis \
        --requirepass root
```

https://gs4.jfcar.com.cn/land/userRegister?callBackUrl=https://gsp.gacmotor.com/h5/html/community/post_details.html?postId=9401057

redis:
121.199.162.237:16380
123456
mysql
121.199.162.237:3306
root/4zAjBTzxXWBw8nZA!@#
172.17.0.1
