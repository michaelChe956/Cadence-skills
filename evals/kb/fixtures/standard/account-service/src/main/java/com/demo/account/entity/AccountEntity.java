package com.demo.account.entity;

/** 账户信息实体（对应 t_user_account） */
public class AccountEntity {
    /** 用户唯一标识（与 t_user.user_id 同源） */
    private Long userId;
    /** 账户号 */
    private String accountNo;
    /** 账户余额，业务规则见表注释：余额不可为负 */
    private java.math.BigDecimal balance;
    /** 账户状态：NORMAL/FROZEN/CLOSED */
    private String status;
}
