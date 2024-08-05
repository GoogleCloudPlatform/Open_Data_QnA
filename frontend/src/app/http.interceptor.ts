import { Injectable } from "@angular/core";
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest, HttpResponse } from "@angular/common/http";
import { Observable, switchMap, tap } from "rxjs";
import { LoginService } from "./shared/services/login.service";

@Injectable()
export class AppHttpInterceptor implements HttpInterceptor {

    userDetails: any;
    idToken!: string;

    constructor(public loginService: LoginService) {
        // this.loginService.getUserDetails().subscribe((res: any) => { this.userDetails = res });
        this.loginService.getIdToken().subscribe((res: string) => {
            console.log(res)
            this.idToken = res
        });
    }

    // intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    //     if (!this.userDetails) {
    //         this.userDetails = this.getUserDetails(req)
    //     }
    //     // Clone the request with necessary headers
    //     const modifiedReq = req.clone({
    //         headers: req.headers
    //             .set('Content-Type', 'application/x-www-form-urlencoded')
    //             .set('Access-Control-Allow-Origin', '*')
    //             .set('Authorization', `Bearer ${this.userDetails?.accessToken}`)
    //     });
    //     const started = Date.now();


    //     return next.handle(modifiedReq).pipe(tap((event: any) => {
    //         const elapsed = Date.now() - started;
    //         //console.log(`Request for ${req.urlWithParams} took ${elapsed} ms.`);
    //         if (event instanceof HttpResponse) {
    //             let responseTime = elapsed / 1000
    //             event.body.responseTime = `${responseTime} s`
    //             return event.body
    //         };
    //     }))
    // }

    // getUserDetails(req: HttpRequest<any>) {
    //     this.loginService.getUserDetails().subscribe((res: any) => {
    //         console.log(res)
    //         this.userDetails = res;
    //     })
    // }

    intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        return this.getUserDetails(req).pipe(
            switchMap((userDetails) => {
                this.userDetails = userDetails;

                const modifiedReq = req.clone({
                    headers: req.headers
                        .set('Content-Type', 'application/x-www-form-urlencoded')
                        .set('Access-Control-Allow-Origin', '*')
                        .set('Authorization', `Bearer ${this.userDetails?.accessToken}`)
                });

                const started = Date.now();

                return next.handle(modifiedReq).pipe(
                    tap((event: any) => {
                        const elapsed = Date.now() - started;
                        // console.log(`Request for ${req.urlWithParams} took ${elapsed} ms.`);
                        if (event instanceof HttpResponse) {
                            let responseTime = elapsed / 1000;
                            event.body.responseTime = `${responseTime} s`;
                            return event.body;
                        }
                    })
                );
            })
        );
    }

    getUserDetails(req: HttpRequest<any>): Observable<any> {
        return this.loginService.getUserDetails();
    }

}