package com.demo.user.service;

import com.demo.user.entity.UserEntity;
import com.demo.user.mapper.UserMapper;
import org.springframework.stereotype.Service;

/** 用户基本信息业务逻辑 */
@Service
public class UserBasicService {

    private final UserMapper userMapper;

    public UserBasicService(UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    /** 按用户 ID 查询基本信息（对应 t_user 表） */
    public UserEntity queryBasic(Long userId) {
        return userMapper.selectById(userId);
    }
}
