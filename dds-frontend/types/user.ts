export interface User {
  id: number;
  username: string;
  email: string;
  role_id: number;
  role_name: string;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

export interface Role {
  id: number;
  name: string;
  description: string;
  permissions: string[];
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  role_id: number;
}
