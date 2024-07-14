import { Injectable } from "@angular/core";
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest, HttpResponse } from "@angular/common/http";
import { Observable, tap } from "rxjs";

@Injectable()
export class AppHttpInterceptor implements HttpInterceptor {
    constructor() { }

    intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        req = req.clone({ headers: req.headers.append('Content-Type', 'application/json') });
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