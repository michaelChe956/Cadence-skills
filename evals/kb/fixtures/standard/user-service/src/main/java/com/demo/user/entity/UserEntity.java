package com.demo.user.entity;

/** 用户基本信息实体（对应 t_user.user_id，见 UserMapper.xml 显式 AS 映射） */
public class UserEntity {
    /** 用户唯一标识 */
    private Long userId;
    private String userName;
    private String mobile;
    private String email;
}
