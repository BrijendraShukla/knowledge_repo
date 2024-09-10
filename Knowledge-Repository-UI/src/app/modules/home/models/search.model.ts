export interface SearchResultResponse {
  tags: string[];
  results: SearchResultData[];
  count: number;
  next?: string | null;
}

export interface SearchResultData {
  id: number;
  file_type: string;
  industry: string[];
  modified_at: Date;
  name: string;
  fileName: string;
  summary: string;
}

export interface SearchStateModel {
  data: SearchResultResponse;

  payload: SearchPayload;
}

export interface SearchPayload {
  query: string;
  file_type?: string | null;
  tags?: string[];
  industry?: string | null;
  date_range_after?: Date | null;
  date_range_before?: Date | null;
  page_size?: number;
  document_type?: string | null;
  generate_tag: boolean;
}
