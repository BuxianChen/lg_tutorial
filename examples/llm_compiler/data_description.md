# 原始赛题

https://tianchi.aliyun.com/competition/entrance/532221/customize456

限制条件
(1) 赛题设计不支持 Text2SQL 

(2) 不允许对 API 进行合并改造, 例如这种做法:
- 组合多个 API 创造新的工具: 例如: 原告是xx公司的案件, 正确做法是 API_6 的话要先查找出关联公司是xx公司的案件, 然后再根据原告做过滤, 但不能创造一个新的工具直接封装这两步.


## API

```python
class CompanyInfo(Base):
    __tablename__ = "company_info"

    公司名称 = Column(Text, primary_key=True, default='')  # 根据主键查询整行数据: API_0
    公司简称 = Column(Text, default='')                    # 根据主键查询整行数据: API_0
    英文名称 = Column(Text, default='')
    关联证券 = Column(Text, default='')
    公司代码 = Column(Text, default='')                    # 根据主键查询整行数据: API_0
    曾用简称 = Column(Text, default='')
    所属市场 = Column(Text, default='')
    所属行业 = Column(Text, default='')
    成立日期 = Column(Text, default='')
    上市日期 = Column(Text, default='')
    法人代表 = Column(Text, default='')
    总经理 = Column(Text, default='')
    董秘 = Column(Text, default='')
    邮政编码 = Column(Text, default='')
    注册地址 = Column(Text, default='')
    办公地址 = Column(Text, default='')
    联系电话 = Column(Text, default='')
    传真 = Column(Text, default='')
    官方网址 = Column(Text, default='')
    电子邮箱 = Column(Text, default='')
    入选指数 = Column(Text, default='')
    主营业务 = Column(Text, default='')
    经营范围 = Column(Text, default='')
    机构简介 = Column(Text, default='')
    每股面值 = Column(Text, default='')
    首发价格 = Column(Text, default='')
    首发募资净额 = Column(Text, default='')
    首发主承销商 = Column(Text, default='')

class CompanyRegister(Base):
    __tablename__ = 'company_register'
    公司名称 = Column(Text, primary_key=True, default='')    # 根据主键查询整行数据: API_1
    登记状态 = Column(Text, default='')
    统一社会信用代码 = Column(Text, default='')               # 查询公司名称: API_2
    法定代表人 = Column(Text, default='')
    注册资本 = Column(Text, default='')
    成立日期 = Column(Text, default='')
    企业地址 = Column(Text, default='')
    联系电话 = Column(Text, default='')
    联系邮箱 = Column(Text, default='')
    注册号 = Column(Text, default='')
    组织机构代码 = Column(Text, default='')
    参保人数 = Column(Text, default='')
    行业一级 = Column(Text, default='')
    行业二级 = Column(Text, default='')
    行业三级 = Column(Text, default='')
    曾用名 = Column(Text, default='')
    企业简介 = Column(Text, default='')
    经营范围 = Column(Text, default='')

class SubCompanyInfo(Base):
    __tablename__ = 'sub_company_info'
    # 母公司名称
    关联上市公司全称 = Column(Text, default='')               # where 条件查询: API_4
    上市公司关系 = Column(Text, default='')
    上市公司参股比例 = Column(Text, default='')
    上市公司投资金额 = Column(Text, default='')
    # 子公司名称
    公司名称 = Column(Text, primary_key=True, default='')    # 根据主键查询整行数据: API_3
    
    
class LegalDoc(Base):
    __tablename__ = 'legal_doc'
    # 关联公司可能是原告或者是被告, 或者都不是
    关联公司 = Column(Text, default='')                     # where 条件查询: API_6
    标题 = Column(Text, default='')
    # 示例: "(2019)沪0115民初61975号"
    案号 = Column(Text, default='', primary_key=True)       # 根据主键查询整行数据: API_5
    文书类型 = Column(Text, default='')
    原告 = Column(Text, default='')
    被告 = Column(Text, default='')
    原告律师事务所 = Column(Text, default='')
    被告律师事务所 = Column(Text, default='')
    案由 = Column(Text, default='')
    涉案金额 = Column(Text, default='')
    判决结果 = Column(Text, default='')
    日期 = Column(Text, default='')
    文件名 = Column(Text, default='')

class CourtInfo(Base):
    __tablename__ = 'court_info'
    法院名称 = Column(Text, default='', primary_key=True)    # 根据主键查询整行数据: API_7
    法院负责人 = Column(Text, default='')
    成立日期 = Column(Text, default='')
    法院地址 = Column(Text, default='')
    法院联系电话 = Column(Text, default='')
    法院官网 = Column(Text, default='')


class CourtCode(Base):
    __tablename__ = 'court_code'
    法院名称 = Column(Text, default='', primary_key=True)    # 根据主键查询整行数据: API_8
    行政级别 = Column(Text, default='')
    法院级别 = Column(Text, default='')
    法院代字 = Column(Text, default='')                      # 根据主键查询整行数据: API_8
    区划代码 = Column(Text, default='')
    级别 = Column(Text, default='')


class LawfirmInfo(Base):
    __tablename__ = 'lawfirm_info'
    律师事务所名称 = Column(Text, default='', primary_key=True)   # 根据主键查询整行数据: API_9
    律师事务所唯一编码 = Column(Text, default='')
    律师事务所负责人 = Column(Text, default='')
    事务所注册资本 = Column(Text, default='')
    事务所成立日期 = Column(Text, default='')
    律师事务所地址 = Column(Text, default='')
    通讯电话 = Column(Text, default='')
    通讯邮箱 = Column(Text, default='')
    律所登记机关 = Column(Text, default='')


class LawfirmLog(Base):
    __tablename__ = 'lawfirm_log'
    律师事务所名称 = Column(Text, default='', primary_key=True)   # 根据主键查询整行数据: API_10
    业务量排名 = Column(Text, default='')
    服务已上市公司 = Column(Text, default='')
    报告期间所服务上市公司违规事件 = Column(Text, default='')
    报告期所服务上市公司接受立案调查 = Column(Text, default='')


class AddrInfo(Base):
    __tablename__ = 'addr_info'
    地址 = Column(Text, default='', primary_key=True)            # 根据主键查询整行数据: API_11
    省份 = Column(Text, default='')
    城市 = Column(Text, default='')
    区县 = Column(Text, default='')


class AddrCode(Base):
    __tablename__ = 'addr_code'
    省份 = Column(Text, default='')
    城市 = Column(Text, default='')
    城市区划代码 = Column(Text, default='')
    区县 = Column(Text, default='')
    区县区划代码 = Column(Text, default='', primary_key=True)      # 根据主键查询整行数据: API_12


class TempInfo(Base):
    __tablename__ = 'temp_info'
    日期 = Column(Text, default='', primary_key=True)              # 根据日期,身份,城市查整行数据: API_13
    省份 = Column(Text, default='', primary_key=True)              
    城市 = Column(Text, default='')
    天气 = Column(Text, default='')
    最高温度 = Column(Text, default='')
    最低温度 = Column(Text, default='')
    湿度 = Column(Text, default='')


class LegalAbstract(Base):
    __tablename__ = 'legal_abstract'
    文件名 = Column(Text, default='')
    案号 = Column(Text, default='', primary_key=True)              # 根据主键查询整行数据: API_14
    文本摘要 = Column(Text, default='')


class XzgxfInfo(Base):
    __tablename__ = 'xzgxf_info'
    限制高消费企业名称 = Column(Text, default='')                   # where 条件查询: API_16
    案号 = Column(Text, default='', primary_key=True)              # 根据主键查询整行数据: API_15
    法定代表人 = Column(Text, default='')
    申请人 = Column(Text, default='')
    涉案金额 = Column(Text, default='')
    执行法院 = Column(Text, default='')
    立案日期 = Column(Text, default='')
    限高发布日期 = Column(Text, default='')

# API_17, API_18: 排序, 算术接口
# API_19, API_20, API_21, API_22, API_23: 写文书接口
```


## 原始问题样例

```python
# 简单题
{"id": 3, "question": "保定市天威西路2222号地址对应的省市区县分别是？"}
{"id": 7, "question": "请问一下，浙江省丽水市景宁畲族自治县对应的区县登记的区划代码是？"}

# 困难题
{"id": 0, "question": "91310000677833266F的公司全称是？该公司的涉案次数为？（起诉日期在2020年）作为被起诉人的次数及总金额为？"}
{"id": 1, "question": "伊吾广汇矿业有限公司作为被告的案件中涉案金额小于100万大于1万的案号分别为？涉案金额数值为？"}
{"id": 2, "question": "请帮我查询一下浙江晨丰科技股份有限公司参与的案件有涉案金额的有哪些？涉案金额总和为？"}
{"id": 9, "question": "机构代码为91110113344302387N的公司涉诉文书中，主要位于哪一年？涉诉文书较多的那一年，和该公司对立方所请最多律师事务所的负责人是？"}
{"id": 20, "question": "(2021)苏0481民初4582号的法院在哪个区县？本题API最优串行调用次数为？"}
```