-- story_nodes 缺失索引补充（性能优化）
-- 用于加速 _current_act_fully_written、context_budget_allocator 图谱查询等热点路径

CREATE INDEX IF NOT EXISTS idx_story_nodes_parent ON story_nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_story_nodes_type ON story_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_story_nodes_novel_type ON story_nodes(novel_id, node_type);
