from managerapp import webapp
from common import models

def set_db_default_values():
    # This function initialzes the database and populates them 
    # with default values if necessary. Do all initialization here because
    # memcache app is being launched ealier
    
    # ensure that the MemcacheConfig table has one and only one
    # entry
    local_session = webapp.db_session()
    memcache_config_default_capacity = 2.0
    memcache_config_default_replacement_policy = "LRU"
    result_count = local_session.query(models.MemcacheConfig).count()
    if(result_count == 0):
        new_entry = models.MemcacheConfig(
            capacity_in_mb = memcache_config_default_capacity,
            replacement_policy = memcache_config_default_replacement_policy
        )
        local_session.add(new_entry)
        local_session.commit()
    elif(result_count > 1):
        assert False, "the MemcacheConfig table should have only one entry!"
    else:
        result = local_session.query(models.MemcacheConfig).first()
        result.replacement_policy = memcache_config_default_replacement_policy
        result.capacity_in_mb = memcache_config_default_capacity
        local_session.commit()

    # ensure that the MemcachePoolResizeConfig table has one and only one
    # entry
    memcache_pool_resize_config_default_mode = "Manual"
    memcache_pool_resize_config_default_max_missrate_threshold = 80
    memcache_pool_resize_config_default_min_missrate_threshold = 20
    memcache_pool_resize_config_default_expand_ratio = 2
    memcache_pool_resize_config_default_shrink_ratio = 0.5
    result_count = local_session.query(models.MemcachePoolResizeConfig).count()
    if(result_count == 0):
        new_entry = models.MemcachePoolResizeConfig(
            resize_mode = memcache_pool_resize_config_default_mode,
            max_missrate_threshold = memcache_pool_resize_config_default_max_missrate_threshold,
            min_missrate_threshold = memcache_pool_resize_config_default_min_missrate_threshold,
            expand_ratio = memcache_pool_resize_config_default_expand_ratio,
            shrink_ratio = memcache_pool_resize_config_default_shrink_ratio,
        )
        local_session.add(new_entry)
        local_session.commit()
    elif(result_count > 1):
        assert False, "the MemcachePoolResizeConfig table should have only one entry!"
    else:
        result = local_session.query(models.MemcachePoolResizeConfig).first()
        result.resize_mode = memcache_pool_resize_config_default_mode,
        result.max_missrate_threshold = memcache_pool_resize_config_default_max_missrate_threshold,
        result.min_missrate_threshold = memcache_pool_resize_config_default_min_missrate_threshold,
        result.expand_ratio = memcache_pool_resize_config_default_expand_ratio,
        result.shrink_ratio = memcache_pool_resize_config_default_shrink_ratio,
        local_session.commit()
