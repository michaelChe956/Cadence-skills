package com.demo.user.controller;

import com.demo.user.entity.UserEntity;
import com.demo.user.service.UserBasicService;
import org.springframework.web.bind.annotation.*;

/** 用户基本信息查询接口（对外能力 API-A） */
@RestController
@RequestMapping("/api/user")
public class UserBasicController {

    private final UserBasicService userBasicService;

    public UserBasicController(UserBasicService userBasicService) {
        this.userBasicService = userBasicService;
    }

    /** 查询用户基本信息：userId、姓名、手机号、邮箱 */
    @GetMapping("/basic/{userId}")
    public UserEntity queryBasic(@PathVariable("userId") Long userId) {
        return userBasicService.queryBasic(userId);
    }
}
