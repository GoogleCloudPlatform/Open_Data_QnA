import { Injectable, inject } from '@angular/core';
import { user } from '@angular/fire/auth';
import { AuthConfig, OAuthService } from 'angular-oauth2-oidc';

@Injectable({
  providedIn: 'root',
})
export class AuthGoogleService {
  private oAuthService = inject(OAuthService);

  constructor() {
    this.initConfiguration();
  }

  initConfiguration() {
    let authConfig: AuthConfig
    if (typeof window !== "undefined")
    // browser code

    {
      authConfig = {
        issuer: 'https://accounts.google.com',
        strictDiscoveryDocumentValidation: false,
        clientId: '978842762722-q8lu91sbb39q4tuh80ca5rpc11fnj0n9.apps.googleusercontent.com',
        redirectUri: window.location.origin + '/dashboard',
        scope: 'openid profile email',
      };
      this.oAuthService.configure(authConfig);
      this.oAuthService.loadDiscoveryDocument().then(() => {
        this.oAuthService.tryLoginImplicitFlow().then(() => {
          if (!this.oAuthService.hasValidAccessToken) {
            this.oAuthService.initLoginFlow()
          } else {
            this.oAuthService.loadUserProfile().then((userprofile) => {
              console.log(userprofile)
            })
          }
        })
      })
      // this.oAuthService.setupAutomaticSilentRefresh();
      // this.oAuthService.loadDiscoveryDocumentAndTryLogin();
    }
  }

  login() {
    this.oAuthService.initImplicitFlow();
  }

  logout() {
    this.oAuthService.revokeTokenAndLogout();
    this.oAuthService.logOut();
  }

  getProfile() {
    const profile = this.oAuthService.getIdentityClaims();
    return profile;
  }

  getToken() {
    return this.oAuthService.getAccessToken();
  }
}