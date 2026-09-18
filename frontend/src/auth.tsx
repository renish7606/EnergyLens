import {createContext,useContext,useEffect,useMemo,useState,type ReactNode} from 'react';

const TOKEN_KEY='energylens_access_token';
type AuthContextValue={token:string|null;isAuthenticated:boolean;login:(token:string)=>void;logout:()=>void};
const AuthContext=createContext<AuthContextValue|undefined>(undefined);

export function AuthProvider({children}:{children:ReactNode}){
  const [token,setToken]=useState<string|null>(()=>localStorage.getItem(TOKEN_KEY));
  useEffect(()=>{const expire=()=>{localStorage.removeItem(TOKEN_KEY);setToken(null)};window.addEventListener('energylens:auth-expired',expire);return()=>window.removeEventListener('energylens:auth-expired',expire)},[]);
  const value=useMemo(()=>({token,isAuthenticated:Boolean(token),login:(next:string)=>{localStorage.setItem(TOKEN_KEY,next);setToken(next)},logout:()=>{localStorage.removeItem(TOKEN_KEY);setToken(null)}}),[token]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth(){const value=useContext(AuthContext);if(!value)throw new Error('useAuth must be used inside AuthProvider');return value}
export {TOKEN_KEY};
