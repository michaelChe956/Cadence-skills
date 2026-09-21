package com.demo.account.controller;

import com.demo.account.entity.AccountEntity;
import com.demo.account.service.AccountService;
import org.springframework.web.bind.annotation.*;

/** 用户账户信息查询接口（对外能力 API-B） */
@RestController
@RequestMapping("/api/account")
public class AccountController {

    private final AccountService accountService;

    public AccountController(AccountService accountService) {
        this.accountService = accountService;
    }

    /** 查询用户账户信息：账户号、余额、状态（对内 REST，供聚合能力复用） */
    @GetMapping("/{userId}")
    public AccountEntity queryAccount(@PathVariable("userId") Long userId) {
        return accountService.queryAccount(userId);
    }
}
