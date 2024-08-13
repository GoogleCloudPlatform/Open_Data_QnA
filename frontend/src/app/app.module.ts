import { CUSTOM_ELEMENTS_SCHEMA, NgModule, importProvidersFrom } from "@angular/core";
import { AppComponent } from "./app.component";
import { LoginComponent } from "./login/login.component";
import { LoginButtonComponent } from "./login-button/login-button.component";
import { LoginService } from "./shared/services/login.service";
import { SharedService } from "./shared/services/shared.service";
import { provideFirestore, initializeFirestore } from "@angular/fire/firestore";
import { getApp, initializeApp, provideFirebaseApp } from "@angular/fire/app";
import { BrowserModule } from "@angular/platform-browser";
import { UserJourneyComponent } from "./user-journey/user-journey.component";
import { AppRoutingModule } from "./app-routing.module";
import { HomeComponent } from "./home/home.component";
import { HeaderComponent } from "./header/header.component";
import { MatToolbarModule } from "@angular/material/toolbar";
import { MatIconModule } from "@angular/material/icon";
import { MatButtonModule } from "@angular/material/button";
import { RouterLink } from "@angular/router";
import { MatTabsModule } from "@angular/material/tabs";
import { MatDividerModule } from "@angular/material/divider";
import { MatSelectModule } from "@angular/material/select";
import { MatInputModule } from "@angular/material/input";
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatAutocompleteModule } from "@angular/material/autocomplete";
import { CommonModule, NgFor, NgIf } from "@angular/common";
import { BrowserAnimationsModule } from "@angular/platform-browser/animations";
import { MatListModule } from '@angular/material/list';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatExpansionModule } from '@angular/material/expansion';
import { MenuComponent } from "./menu/menu.component";
import { FormsModule, ReactiveFormsModule } from "@angular/forms";
import { BusinessUserComponent } from "./business-user/business-user.component";
import { MatTableModule } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { HTTP_INTERCEPTORS, HttpClientModule, provideHttpClient, withFetch } from '@angular/common/http';
import { HomeService } from './shared/services/home.service';
import { provideAuth, getAuth } from '@angular/fire/auth';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { OperationalUserComponent } from './operational-user/operational-user.component';
import { NgChartsModule } from 'ng2-charts';
import { ReportsComponent } from './reports/reports.component';
import { TechnicalUserComponent } from './technical-user/technical-user.component';
import { AngularFireModule } from '@angular/fire/compat';
import { AngularFirestoreModule } from '@angular/fire/compat/firestore';
import { AngularFireAuth, AngularFireAuthModule } from '@angular/fire/compat/auth';
import { UserPhotoComponent } from "./user-photo/user-photo.component";
import { PrismComponent } from "./prism/prism.component";
import 'prismjs/components/prism-sql';
import { MatPaginatorModule } from "@angular/material/paginator";
import { OverlayModule } from "@angular/cdk/overlay";
import { SavedQueriesComponent } from './saved-queries/saved-queries.component';
import { GoogleChartsModule } from "angular-google-charts";
import { MatRadioModule } from '@angular/material/radio';
import { MatStepperModule } from '@angular/material/stepper';
import { STEPPER_GLOBAL_OPTIONS } from "@angular/cdk/stepper";
import { AgentChatComponent } from "./agent-chat/agent-chat.component";
import { AppHttpInterceptor } from "./http.interceptor";
import { firebaseConfig, FIRESTORE_DATABASE_ID } from "../assets/constants";
import { MatTreeModule } from "@angular/material/tree";
import { ScenarioListComponent } from "./scenario-list/scenario-list.component";
import { provideOAuthClient } from "angular-oauth2-oidc"
import { DashboardComponent } from "./dashboard/dashboard.component";
import { AuthGoogleService } from "./shared/services/auth-google.service";
import { SigninComponent } from "./signin/signin.component";

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    LoginButtonComponent,
    UserJourneyComponent,
    HomeComponent,
    HeaderComponent,
    MenuComponent,
    BusinessUserComponent,
    OperationalUserComponent,
    ReportsComponent,
    TechnicalUserComponent,
    UserPhotoComponent,
    PrismComponent,
    SavedQueriesComponent,
    AgentChatComponent,
    ScenarioListComponent,
    DashboardComponent,
SigninComponent
  ],
  imports: [
    CommonModule,
    BrowserModule,
    ReactiveFormsModule,
    FormsModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    MatToolbarModule,
    MatIconModule,
    MatButtonModule,
    RouterLink,
    MatTabsModule,
    MatDividerModule,
    NgIf,
    NgFor,
    MatSelectModule,
    MatInputModule,
    MatFormFieldModule,
    MatAutocompleteModule,
    MatListModule,
    MatSidenavModule,
    MatTableModule,
    MatExpansionModule,
    MatCardModule,
    HttpClientModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    ClipboardModule,
    MatSlideToggleModule,
    NgChartsModule,
    AngularFireModule.initializeApp(firebaseConfig),
    AngularFirestoreModule,
    AngularFireAuthModule,
    MatPaginatorModule,
    OverlayModule,
    GoogleChartsModule,
    MatRadioModule,
    MatStepperModule,
    MatExpansionModule,
    MatTreeModule
  ],
  providers: [
    {
      provide: STEPPER_GLOBAL_OPTIONS,
      useValue: { displayDefaultIndicatorType: false }
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AppHttpInterceptor,
      multi: true
    },
    provideHttpClient(withFetch()),
    importProvidersFrom([
      provideFirebaseApp(() => initializeApp(firebaseConfig)),
      provideFirestore(() => {
        const app = getApp();
        const providedFirestore = initializeFirestore(app, {}, FIRESTORE_DATABASE_ID);
        return providedFirestore;
      }),

      provideAuth(() => getAuth()),
      
      LoginService,
      SharedService,
      HomeService,
      AngularFireAuth,
      
    ]),
    AuthGoogleService,
    provideOAuthClient(),
  ],
  bootstrap: [AppComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class AppModule { }