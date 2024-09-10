export interface logInPayload {
  username: string;
  password: string;
}
export interface logInApiResponse {
  token: string;
  user: user;
}
export interface user {
  id: number;
  email: string;
  name: string;
}
