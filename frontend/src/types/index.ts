// API Types

export interface City {
  id: number;
  name: string;
  province: string;
  tier: "tier1" | "new_tier1" | "tier2" | "tier3";
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Keyword {
  id: number;
  category: "job_search" | "job_exclude" | "forum_topic";
  keyword: string;
  priority: "core" | "extended";
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataSource {
  id: number;
  name: string;
  type: "job" | "rent" | "forum" | "public_data";
  slug: string;
  enabled: boolean;
  priority: number;
  config: Record<string, unknown>;
  last_success_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface CrawlTask {
  id: string;
  task_type: string;
  data_source_id: number | null;
  city_id: number | null;
  keyword_id: number | null;
  status: "pending" | "running" | "success" | "failed" | "cancelled";
  progress: number;
  records_count: number;
  error_message: string | null;
  celery_task_id: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  // Related names for display
  data_source_name?: string | null;
  city_name?: string | null;
  keyword_text?: string | null;
}

export type TaskType = "job_crawl" | "rent_crawl" | "forum_crawl" | "public_data";
export type TaskStatus = "pending" | "running" | "success" | "failed" | "cancelled";

export interface CrawlTaskCreate {
  task_type: TaskType;
  data_source_id?: number | null;
  city_id?: number | null;
  keyword_id?: number | null;
}

export interface CrawlTaskUpdate {
  status?: TaskStatus;
  progress?: number;
  records_count?: number;
  error_message?: string;
}

export interface BatchTaskCreate {
  task_type: TaskType;
  data_source_id: number;
  city_ids?: number[] | null;
  keyword_id?: number | null;
}

export interface TaskStats {
  pending: number;
  running: number;
  success: number;
  failed: number;
  cancelled: number;
  total_records: number;
}

// Request types
export interface CityCreate {
  name: string;
  province: string;
  tier?: City["tier"];
  enabled?: boolean;
}

export interface CityUpdate {
  name?: string;
  province?: string;
  tier?: City["tier"];
  enabled?: boolean;
}

export interface KeywordCreate {
  category: Keyword["category"];
  keyword: string;
  priority?: Keyword["priority"];
  enabled?: boolean;
}

export interface KeywordUpdate {
  category?: Keyword["category"];
  keyword?: string;
  priority?: Keyword["priority"];
  enabled?: boolean;
}

export interface DataSourceCreate {
  name: string;
  type: DataSource["type"];
  slug: string;
  enabled?: boolean;
  priority?: number;
  config?: Record<string, unknown>;
}

export interface DataSourceUpdate {
  name?: string;
  type?: DataSource["type"];
  slug?: string;
  enabled?: boolean;
  priority?: number;
  config?: Record<string, unknown>;
}

// Manual Import Types
export type ImportDataType = "job" | "rent" | "forum";

export interface PlatformSearchGuide {
  platform: string;
  platform_name: string;
  description: string;
  search_urls: Array<{
    city: string;
    keyword: string;
    url: string;
  }>;
  tips: string[];
}

export interface ImportPreviewResponse {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  errors: Array<{
    row: number;
    field: string;
    error: string;
  }>;
  preview: Array<Record<string, unknown>>;
}

export interface ImportResultResponse {
  success: boolean;
  imported_count: number;
  skipped_count: number;
  errors: Array<{
    row: number;
    error: string;
  }>;
}

export interface ImportRequest {
  data_type: ImportDataType;
  city_id: number;
  data_source_id: number;
  rows: Array<Record<string, unknown>>;
}

// Paginated Response
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// Job Types
export interface JobListItem {
  id: string;
  title: string;
  company: string | null;
  district: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_raw: string | null;
  experience: string | null;
  education: string | null;
  tags: string | null;
  posted_at: string | null;
  crawled_at: string;
  city_name: string | null;
  data_source_name: string | null;
}

export interface Job extends JobListItem {
  company_type: string | null;
  company_size: string | null;
  address: string | null;
  description: string | null;
  benefits: string | null;
  data_source_id: number;
  city_id: number;
  crawl_task_id: string | null;
  source_id: string;
  source_url: string | null;
}

export interface JobStats {
  total: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
  min_salary: number | null;
  max_salary: number | null;
}

// Rent Types
export interface RentListItem {
  id: string;
  title: string;
  property_type: string | null;
  district: string | null;
  neighborhood: string | null;
  price: number | null;
  price_raw: string | null;
  area: number | null;
  layout: string | null;
  subway_info: string | null;
  posted_at: string | null;
  crawled_at: string;
  city_name: string | null;
  data_source_name: string | null;
}

export interface Rent extends RentListItem {
  address: string | null;
  payment_type: string | null;
  area_raw: string | null;
  floor: string | null;
  orientation: string | null;
  decoration: string | null;
  description: string | null;
  facilities: string | null;
  data_source_id: number;
  city_id: number;
  crawl_task_id: string | null;
  source_id: string;
  source_url: string | null;
  images: string | null;
  agent_name: string | null;
  agent_phone: string | null;
}

export interface RentStats {
  total: number;
  avg_price: number | null;
  min_price: number | null;
  max_price: number | null;
  avg_area: number | null;
}

// Forum Types
export interface ForumPostListItem {
  id: string;
  title: string | null;
  content: string;
  author: string | null;
  topic: string | null;
  likes: number;
  replies_count: number;
  post_type: string;
  source_url: string | null;
  posted_at: string | null;
  crawled_at: string;
  city_name: string | null;
  data_source_name: string | null;
}

export interface ForumPost extends ForumPostListItem {
  tags: string | null;
  views: number;
  data_source_id: number;
  city_id: number | null;
  crawl_task_id: string | null;
  source_id: string;
  parent_id: string | null;
  author_id: string | null;
  search_keyword: string | null;
  sentiment: string | null;
}

export interface ForumStats {
  total: number;
  total_likes: number;
  total_replies: number;
  avg_likes: number | null;
  by_type: Record<string, number>;
}

// Analysis Types
export interface CityComparisonItem {
  city_id: number;
  city_name: string;
  province: string;
  tier: string;
  job_count: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
  avg_salary: number | null;
  rent_count: number;
  avg_rent: number | null;
  min_rent: number | null;
  max_rent: number | null;
  avg_area: number | null;
  post_count: number;
  total_likes: number;
  total_replies: number;
  salary_rent_ratio: number | null;
}

export interface CityComparisonResponse {
  cities: { id: number; name: string; province: string; tier: string }[];
  comparison: CityComparisonItem[];
}

export interface RankingItem {
  rank: number;
  city_id: number;
  city_name: string;
  province: string;
  value: number;
  sample_size?: number;
}

export interface RankingsResponse {
  dimension: string;
  label: string;
  unit: string;
  rankings: RankingItem[];
}

export interface CityScore {
  rank: number;
  city_id: number;
  city_name: string;
  province: string;
  tier: string;
  composite_score: number;
  salary_score: number;
  rent_score: number;
  ratio_score: number;
  forum_score: number;
  avg_salary: number | null;
  avg_rent: number | null;
  salary_rent_ratio: number | null;
  post_count: number;
}

export interface ScoresResponse {
  weights: Record<string, number>;
  scores: CityScore[];
}

export interface AiReportResponse {
  prompt: string;
  city_count: number;
  generated_at: string;
}

// Re-export WebSocket types
export * from "./websocket";
