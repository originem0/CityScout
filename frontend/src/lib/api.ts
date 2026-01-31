const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      error.detail || `HTTP error ${response.status}`
    );
  }

  return response.json();
}

export const api = {
  // Cities
  cities: {
    list: (params?: { enabled?: boolean; tier?: string }) =>
      request<import("@/types").City[]>(
        `/api/v1/cities${params ? `?${new URLSearchParams(params as Record<string, string>)}` : ""}`
      ),
    get: (id: number) => request<import("@/types").City>(`/api/v1/cities/${id}`),
    create: (data: import("@/types").CityCreate) =>
      request<import("@/types").City>("/api/v1/cities", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: number, data: import("@/types").CityUpdate) =>
      request<import("@/types").City>(`/api/v1/cities/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      request<{ message: string }>(`/api/v1/cities/${id}`, { method: "DELETE" }),
    toggle: (id: number) =>
      request<import("@/types").City>(`/api/v1/cities/${id}/toggle`, {
        method: "PATCH",
      }),
  },

  // Keywords
  keywords: {
    list: (params?: { category?: string; enabled?: boolean; priority?: string }) =>
      request<import("@/types").Keyword[]>(
        `/api/v1/keywords${params ? `?${new URLSearchParams(params as Record<string, string>)}` : ""}`
      ),
    get: (id: number) => request<import("@/types").Keyword>(`/api/v1/keywords/${id}`),
    create: (data: import("@/types").KeywordCreate) =>
      request<import("@/types").Keyword>("/api/v1/keywords", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: number, data: import("@/types").KeywordUpdate) =>
      request<import("@/types").Keyword>(`/api/v1/keywords/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      request<{ message: string }>(`/api/v1/keywords/${id}`, { method: "DELETE" }),
  },

  // Data Sources
  sources: {
    list: (params?: { type?: string; enabled?: boolean }) =>
      request<import("@/types").DataSource[]>(
        `/api/v1/sources${params ? `?${new URLSearchParams(params as Record<string, string>)}` : ""}`
      ),
    get: (id: number) =>
      request<import("@/types").DataSource>(`/api/v1/sources/${id}`),
    create: (data: import("@/types").DataSourceCreate) =>
      request<import("@/types").DataSource>("/api/v1/sources", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: number, data: import("@/types").DataSourceUpdate) =>
      request<import("@/types").DataSource>(`/api/v1/sources/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      request<{ message: string }>(`/api/v1/sources/${id}`, { method: "DELETE" }),
    toggle: (id: number) =>
      request<import("@/types").DataSource>(`/api/v1/sources/${id}/toggle`, {
        method: "PATCH",
      }),
  },

  // Tasks
  tasks: {
    list: (params?: {
      status?: string;
      task_type?: string;
      city_id?: number;
      data_source_id?: number;
      skip?: number;
      limit?: number;
    }) => {
      const searchParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined) {
            searchParams.set(key, String(value));
          }
        });
      }
      const query = searchParams.toString();
      return request<import("@/types").CrawlTask[]>(
        `/api/v1/tasks${query ? `?${query}` : ""}`
      );
    },
    get: (id: string) =>
      request<import("@/types").CrawlTask>(`/api/v1/tasks/${id}`),
    create: (data: import("@/types").CrawlTaskCreate) =>
      request<import("@/types").CrawlTask>("/api/v1/tasks", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    createBatch: (data: import("@/types").BatchTaskCreate) =>
      request<import("@/types").CrawlTask[]>("/api/v1/tasks/batch", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: import("@/types").CrawlTaskUpdate) =>
      request<import("@/types").CrawlTask>(`/api/v1/tasks/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<{ message: string }>(`/api/v1/tasks/${id}`, { method: "DELETE" }),
    start: (id: string) =>
      request<import("@/types").CrawlTask>(`/api/v1/tasks/${id}/start`, {
        method: "POST",
      }),
    cancel: (id: string) =>
      request<import("@/types").CrawlTask>(`/api/v1/tasks/${id}/cancel`, {
        method: "POST",
      }),
    stats: () =>
      request<import("@/types").TaskStats>("/api/v1/tasks/stats/summary"),
  },

  // Manual Import
  import: {
    getGuide: (params?: { city_ids?: string; keyword_category?: string }) => {
      const searchParams = new URLSearchParams();
      if (params?.city_ids) searchParams.set("city_ids", params.city_ids);
      if (params?.keyword_category) searchParams.set("keyword_category", params.keyword_category);
      const query = searchParams.toString();
      return request<import("@/types").PlatformSearchGuide[]>(
        `/api/v1/import/guide${query ? `?${query}` : ""}`
      );
    },
    getTemplateUrl: (dataType: string) =>
      `${API_BASE_URL}/api/v1/import/template/${dataType}`,
    preview: async (file: File, dataType: string, cityId: number, dataSourceId: number) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("data_type", dataType);
      formData.append("city_id", String(cityId));
      formData.append("data_source_id", String(dataSourceId));

      const response = await fetch(`${API_BASE_URL}/api/v1/import/preview`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(response.status, error.detail || "Preview failed");
      }

      return response.json() as Promise<import("@/types").ImportPreviewResponse>;
    },
    execute: async (file: File, dataType: string, cityId: number, dataSourceId: number) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("data_type", dataType);
      formData.append("city_id", String(cityId));
      formData.append("data_source_id", String(dataSourceId));

      const response = await fetch(`${API_BASE_URL}/api/v1/import/execute`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(response.status, error.detail || "Import failed");
      }

      return response.json() as Promise<import("@/types").ImportResultResponse>;
    },
    importJson: (data: import("@/types").ImportRequest) =>
      request<import("@/types").ImportResultResponse>("/api/v1/import/json", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  // Jobs Data
  jobs: {
    list: (params?: {
      skip?: number;
      limit?: number;
      city_id?: number;
      data_source_id?: number;
      search?: string;
      district?: string;
      salary_min?: number;
      salary_max?: number;
      sort_by?: string;
      sort_order?: string;
    }) => {
      const searchParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== "") {
            searchParams.set(key, String(value));
          }
        });
      }
      const query = searchParams.toString();
      return request<import("@/types").PaginatedResponse<import("@/types").JobListItem>>(
        `/api/v1/jobs${query ? `?${query}` : ""}`
      );
    },
    get: (id: string) => request<import("@/types").Job>(`/api/v1/jobs/${id}`),
    stats: (cityId?: number) => {
      const query = cityId ? `?city_id=${cityId}` : "";
      return request<import("@/types").JobStats>(`/api/v1/jobs/stats/summary${query}`);
    },
  },

  // Rent Data
  rent: {
    list: (params?: {
      skip?: number;
      limit?: number;
      city_id?: number;
      data_source_id?: number;
      search?: string;
      district?: string;
      property_type?: string;
      price_min?: number;
      price_max?: number;
      area_min?: number;
      area_max?: number;
      sort_by?: string;
      sort_order?: string;
    }) => {
      const searchParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== "") {
            searchParams.set(key, String(value));
          }
        });
      }
      const query = searchParams.toString();
      return request<import("@/types").PaginatedResponse<import("@/types").RentListItem>>(
        `/api/v1/rent${query ? `?${query}` : ""}`
      );
    },
    get: (id: string) => request<import("@/types").Rent>(`/api/v1/rent/${id}`),
    stats: (cityId?: number) => {
      const query = cityId ? `?city_id=${cityId}` : "";
      return request<import("@/types").RentStats>(`/api/v1/rent/stats/summary${query}`);
    },
  },

  // Forum Data
  forum: {
    list: (params?: {
      skip?: number;
      limit?: number;
      city_id?: number;
      data_source_id?: number;
      search?: string;
      topic?: string;
      post_type?: string;
      author?: string;
      sort_by?: string;
      sort_order?: string;
    }) => {
      const searchParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== "") {
            searchParams.set(key, String(value));
          }
        });
      }
      const query = searchParams.toString();
      return request<import("@/types").PaginatedResponse<import("@/types").ForumPostListItem>>(
        `/api/v1/forum${query ? `?${query}` : ""}`
      );
    },
    get: (id: string) => request<import("@/types").ForumPost>(`/api/v1/forum/${id}`),
    stats: (cityId?: number) => {
      const query = cityId ? `?city_id=${cityId}` : "";
      return request<import("@/types").ForumStats>(`/api/v1/forum/stats/summary${query}`);
    },
  },

  // Analysis
  analysis: {
    cityComparison: (cityIds?: number[]) => {
      const query = cityIds?.length ? `?city_ids=${cityIds.join(",")}` : "";
      return request<import("@/types").CityComparisonResponse>(
        `/api/v1/analysis/city-comparison${query}`
      );
    },
    rankings: (dimension: string, limit?: number) => {
      const params = new URLSearchParams({ dimension });
      if (limit) params.set("limit", String(limit));
      return request<import("@/types").RankingsResponse>(
        `/api/v1/analysis/rankings?${params}`
      );
    },
    scores: (weights?: string) => {
      const query = weights ? `?weights=${weights}` : "";
      return request<import("@/types").ScoresResponse>(
        `/api/v1/analysis/score${query}`
      );
    },
  },

  // Export
  export: {
    cityComparisonCsvUrl: (cityIds?: number[]) => {
      const query = cityIds?.length ? `?city_ids=${cityIds.join(",")}` : "";
      return `${API_BASE_URL}/api/v1/export/excel/city-comparison${query}`;
    },
    forumSummaryMdUrl: (cityId?: number, limit?: number) => {
      const params = new URLSearchParams();
      if (cityId) params.set("city_id", String(cityId));
      if (limit) params.set("limit", String(limit));
      const query = params.toString();
      return `${API_BASE_URL}/api/v1/export/markdown/forum-summary${query ? `?${query}` : ""}`;
    },
    aiReport: (cityIds?: number[]) => {
      const query = cityIds?.length ? `?city_ids=${cityIds.join(",")}` : "";
      return request<import("@/types").AiReportResponse>(
        `/api/v1/export/ai-report${query}`
      );
    },
  },

  // Health check
  health: () => request<{ status: string; project: string }>("/health"),
};
