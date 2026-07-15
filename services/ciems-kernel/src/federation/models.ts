export interface Realm { realmId:string; name:string; allowedGraphs:string[] }
export interface RealmFederationPolicy { fromRealmId:string; toRealmId:string; allowedGraphTypes:string[]; governanceProfile:string }
