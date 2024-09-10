export interface MyContributionApiResponse {
  message: string;
  results: myContribution[];
  count: number;
  next: string | null;
}

export interface myContributionData {
  results: myContribution[];
  count: number;
  next?: string | null;
}
export interface myContribution {
  id: number;
  name: string;
  industry_output: { industry: string }[];
  file_type: string;
  summary: string;
  tags_output: { name: string };
  document_type_output: { document_type: string };
}

export interface myContributionPayload {
  date_range_after?: Date | null;
  date_range_before?: Date | null;
  file_type?: string | null;
  industry?: string | null;
  document_type?: string;
  // pageSize?: number;
  // pageNumber?: number;
}

export interface MyContributionStateModel {
  data: myContributionData;
  payload: myContributionPayload;
}

export interface FileUploadApiResponse {
  documents: {
    file_type: string;
    industry_type: string[];
    tags: string[];
    summary: string;
  }[];
}
