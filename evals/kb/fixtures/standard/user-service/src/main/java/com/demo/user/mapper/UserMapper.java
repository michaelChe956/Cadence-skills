package com.demo.user.mapper;

import com.demo.user.entity.UserEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/** t_user 表数据访问 */
@Mapper
public interface UserMapper {
    UserEntity selectById(@Param("userId") Long userId);
}
