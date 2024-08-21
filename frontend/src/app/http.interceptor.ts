import { Injectable, inject } from "@angular/core";
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest, HttpResponse } from "@angular/common/http";
import { Observable, Subscription, tap } from "rxjs";
import { LoginService } from "./shared/services/login.service";
import { Auth, User, user } from "@angular/fire/auth";
import { Dialog } from "@angular/cdk/dialog";

@Injectable()
export class AppHttpInterceptor implements HttpInterceptor {

    userDetails: any;
    idToken!: string;
    private auth: Auth = inject(Auth);
    user$ = user(this.auth);
    userSubscription: Subscription;


    constructor(public loginService: LoginService, public dialog: Dialog) {
        this.userSubscription = this.user$.subscribe((aUser: User | null) => {
            //handle user state changes here. Note, that user will be null if there is no currently logged in user
            if (aUser) {
                this.dialog.closeAll();
                console.log(aUser)
                this.loginService.sendUserDetails(aUser)
            }

        })
        this.loginService.getUserDetails().subscribe((res: any) => {
            console.log("Access Token", res.accessToken)
            this.userDetails = res
        });
        this.loginService.getIdToken().subscribe((res: string) => {
            this.idToken = res
        });
    }

    intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        req = req.clone({ headers: req.headers.append('Content-Type', 'application/x-www-form-urlencoded') });
        req = req.clone({ headers: req.headers.append('Access-Control-Allow-Origin', '*') });
        req = req.clone({ headers: req.headers.append('Access-Control-Allow-Headers', '*') });
        req = req.clone({ headers: req.headers.append('Authorization', `Bearer ${this.userDetails.accessToken || this.idToken}`) });
        const started = Date.now();
        return next.handle(req).pipe(tap((event: any) => {
            const elapsed = Date.now() - started;
            //console.log(`Request for ${req.urlWithParams} took ${elapsed} ms.`);
            if (event instanceof HttpResponse) {
                let responseTime = elapsed / 1000
                event.body.responseTime = `${responseTime} s`
                return event.body
            };
        })
        )
    }

}