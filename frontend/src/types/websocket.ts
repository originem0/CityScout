// WebSocket types for real-time task progress

export interface TaskProgressData {
  status: string;
  progress: number;
  records_count: number;
  current_state: string;
  current_page: number;
  total_pages: number | null;
  items_found: number;
  items_failed: number;
  error_message: string | null;
  error_type: string | null;
  completed?: boolean;
}

export interface WsProgressMessage {
  type: "progress";
  task_id: string;
  data: TaskProgressData;
  timestamp: string;
}

export interface WsInitialMessage {
  type: "initial";
  task_id: string;
  data: TaskProgressData;
}

export interface WsCompletedMessage {
  type: "completed";
  task_id: string;
  data: TaskProgressData;
}

export interface WsHeartbeatMessage {
  type: "heartbeat";
}

export interface WsErrorMessage {
  type: "error";
  message: string;
}

export type WsMessage =
  | WsProgressMessage
  | WsInitialMessage
  | WsCompletedMessage
  | WsHeartbeatMessage
  | WsErrorMessage;

// Task state labels for UI
export const TASK_STATE_LABELS: Record<string, string> = {
  init: "初始化",
  connecting: "连接中",
  loading: "加载页面",
  parsing: "解析数据",
  saving: "保存数据",
  paginating: "翻页中",
  completed: "已完成",
  failed: "失败",
};
