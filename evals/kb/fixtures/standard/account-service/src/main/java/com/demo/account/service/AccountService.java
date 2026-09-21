package com.demo.account.service;

import com.demo.account.entity.AccountEntity;
import com.demo.account.mapper.AccountMapper;
import org.springframework.stereotype.Service;

/** 账户信息业务逻辑 */
@Service
public class AccountService {

    private final AccountMapper accountMapper;

    public AccountService(AccountMapper accountMapper) {
        this.accountMapper = accountMapper;
    }

    /** 按用户 ID 查询账户（对应 t_user_account 表） */
    public AccountEntity queryAccount(Long userId) {
        return accountMapper.selectByUserId(userId);
    }
}
