from django.contrib import admin
from webopenface.models import Person, PeopleFace, DetectedPeople, DetectedFace, Frame


class PersonAdmin(admin.ModelAdmin):
    date_hierarchy = 'add_date'
    list_filter = ['add_date']
    list_display = ('name', 'uid', 'mod_date')
    fieldsets = [
        (None,               {'fields': ['uid', 'name']}),
        # ('Date information', {'fields': ['add_date', 'mod_date']}),
    ]


class PeopleFaceAdmin(admin.ModelAdmin):
    list_display = ('person', 'face')


class DetectedPeopleAdmin(admin.ModelAdmin):
    list_display = ('person', 'face')


class FrameAdmin(admin.ModelAdmin):
    date_hierarchy = 'add_date'
    list_filter = ['add_date']
    list_display = ('frame', 'add_date')


class DetectedFaceAdmin(admin.ModelAdmin):
    list_display = ('face', 'frame')

admin.site.register(Person, PersonAdmin)
admin.site.register(PeopleFace, PeopleFaceAdmin)
admin.site.register(DetectedPeople, DetectedPeopleAdmin)
admin.site.register(DetectedFace, DetectedFaceAdmin)
admin.site.register(Frame, FrameAdmin)
