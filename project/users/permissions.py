from rest_framework.permissions import BasePermission

class IsStateAdmin(BasePermission):

    def has_permission(self,request,view):
        return request.user.role.name=='STATE_ADMIN'

class IsDistrictAdmin(BasePermission):

    def has_permission(self,request,view):
        return request.user.role.name=='DISTRICT_ADMIN'