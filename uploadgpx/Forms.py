from django import forms
from uploadgpx.models import GpxFile
# from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext as _  #Deprecated. Need to update

class UploadGpxForm(forms.ModelForm):

    title = forms.CharField(max_length=100)
    gpx_file = forms.FileField(required='FALSE')


    class Meta:
        model = GpxFile
        fields = ['title', 'gpx_file']

    def clean_gpx_file(self):
        uploaded_file = self.cleaned_data['gpx_file']
       # print (uploaded_file.content_type)

        content_type = uploaded_file.content_type #check method
        allowed_content_types = ['text/xml', 'application/octet-stream'] #check this
        if content_type not in allowed_content_types:
            raise forms.ValidationError(_('Filetype not supported'))
          #  if uploaded_file._size > 261440: #check this. Seems low and wrong
           #     raise forms.ValidationError(_('Please keep filesize under 2.5 MB. Current filesize %s') % (filesizeformat(uploaded_file._size)))

        #else:
            
        
        return uploaded_file