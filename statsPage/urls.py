from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView

urlpatterns = patterns('statsPage.views',
    # /
    url(r'^$','show_log'),
    url(r'^help/$','help'),

    # Action Stats
    url(r'^nested_d3/$','nested_d3'),

    # World Stats
    url(r'^table/$','table'),
    url(r'^world_stats/$','world_stats'),
    url(r'^geo_stats/$','geo_stats'),

    # Time Stats
    url(r'^all_years_pie/$','all_years_pie'),
    url(r'^pie_by_year/$','pie_by_year'),

    # Session Stats
    url(r'^platform_bar/$','platform_bar'),
    url(r'^bar_session/$','bar_session'),
    url(r'^sessions_started_per_day/$','sessions_started_per_day'),
    url(r'^unique_user_session/$','unique_user_session'),

    # Survey
    url(r'^survey/$','survey'),
    url(r'^survey_results/$','survey_results'),
    url(r'^results_installProc/$','results_installProc'),
    url(r'^results_cdat_pack/$','results_cdat_pack'),
    url(r'^results_packageUsage/$','results_packageUsage'),
    url(r'^results_mostUsed/$','results_mostUsed'),
    url(r'^results_mostUsed/$','results_mostUsed'),
    url(r'^response_time/$','response_time'),
    url(r'^cdat_used_for/$','cdat_used_for'),
    url(r'^commandLine_UI/$','commandLine_UI'),
    url(r'^fav_OS/$','fav_OS'),
    url(r'^gui_dis_like/$','gui_dis_like'),
    url(r'^useOnWindows/$','useOnWindows'),
    url(r'^dataFileFormat/$','dataFileFormat'),
    url(r'^otherTools/$','otherTools'),
    url(r'^userSupportUsefulness/$','userSupportUsefulness'),
    url(r'^graphicsMostUsed/$','graphicsMostUsed'),
    url(r'^averageTimeToPlot/$','averageTimeToPlot'),
    url(r'^howOftenUsed/$','howOftenUsed'),
    url(r'^dataFormatConvention/$','dataFormatConvention'),
    url(r'^youTubeHelp/$','youTubeHelp'),
    url(r'^docUsefulness/$','docUsefulness'),
    url(r'^galleryUsefulness/$','galleryUsefulness'),
    url(r'^fileFormat/$','fileFormat'),
    url(r'^analysisAvgLength/$','analysisAvgLength'),
    url(r'^additionalConcerns/$','additionalConcerns'),
    url(r'^sizeOfDataFiles/$','sizeOfDataFiles'),
    url(r'^cmndline/$','cmndline'),
    url(r'^whichFeature/$','whichFeature'),
    url(r'^guiUsefulness/$','guiUsefulness'),
    url(r'^otherVizGraphics/$','otherVizGraphics'),
    url(r'^improvements/$','improvements'),
    url(r'^python3comp/$','python3comp'),
    url(r'^userAwareness/$','userAwareness'),
    url(r'^YesUserAwareness/$','YesUserAwareness'),
    url(r'^NoUserAwareness/$','NoUserAwareness'),
    url(r'^subPackageUsage/$','subPackageUsage'),

    url(r'^testing/$','testing'),

    # /log/errors
    url(r'^errors/$','show_error_log'),

    # /log/error/203215
    url(r'^error/(?P<error_id>\d+)/$','show_error_details'),

    # /log/login/
    url(r'^login/$','show_sign_in_page'),

    # /log/debug/
    url(r'^debug/$', 'show_debug'),

    # /log/debugerr/
    url(r'^debugerr/$', 'show_debug_error'),
)
