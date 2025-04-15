from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

class PreventAutoLoginMiddleware(MiddlewareMixin):
    def process_request(self, request):
        
        if request.user.is_authenticated and not request.session.get('redirected_to_admin', False):
        
            if request.user.is_superuser and not request.session.get('auto_login', False):
            
                request.session['redirected_to_admin'] = True

                return redirect('admin:index')  

            if request.user.is_superuser and request.session.get('auto_login', False):
                print(f"[DEBUG] Preventing auto-login for user: {request.user.username}")
                del request.session['auto_login']  
                return redirect('admin:login') 

        return None  
