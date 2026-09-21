package com.demo.account.mapper;

import com.demo.account.entity.AccountEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/** t_user_account 表数据访问 */
@Mapper
public interface AccountMapper {
    AccountEntity selectByUserId(@Param("userId") Long userId);
}
