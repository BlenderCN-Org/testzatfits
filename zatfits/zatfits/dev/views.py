
import datetime

from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import authenticate, login, logout as contriblogout
from django import forms
from django.contrib.staticfiles.templatetags.staticfiles import static

from users.models import User, Country, City, Region
from servermanager.tasks import ServerManager, generate_model, scaleTest, fittingProcessus, mypath_ZT

import os

import xml.etree.ElementTree as ET
# mandrill -> y0Q4bYU3dBRrss4AfMAhoQ

class LoginForm(forms.Form):
    email_attr = {'class': 'form-control', 'placeholder': 'Email', 'style': 'margin-bottom:10px;','required':'True',}
    password_attr = {'class': 'form-control', 'placeholder': 'Password', 'style': 'margin-bottom:10px;','required':'True',}

    email = forms.EmailField(label='Email', widget=forms.TextInput(attrs=email_attr), required=True)
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(attrs=password_attr), required=True)

    class Meta:
        models= User
        fields=("email","password")

    def clean_password(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        print(password)
        if email and password:
            user = authenticate(username=email, password=password)
            if user is not None:
                if not user.is_active:
                    raise forms.ValidationError('Compte desactive')
                else:
                    return password
            else:
                raise forms.ValidationError('Identifiants incorrects')

def connexion(request):
    if request.method == 'POST':
        loginform = LoginForm(request.POST)
        if loginform.is_valid():
            email = loginform.cleaned_data['email']
            password = loginform.cleaned_data['password']
            print(password)
            user = authenticate(username=email, password=password)
            login(request, user)
            return redirect('dev:index')
        else:
            context = RequestContext(request)
            context_dict = {}
            context_dict['loginform'] = loginform
            return render_to_response('dev/index.html', context_dict, context)
    else:
        return redirect('dev:index')


class SubscriptionForm(forms.Form):

    error_messages={
        'email_used' : 'Cet Email a déjà été utilisé',
        'not_city':'Vous devez entrer une Ville en cliquant sur le menu déroulant',
    }
    #first_name_attr = {'class': 'form-control', 'placeholder': 'Prénom', 'style': 'margin-bottom:10px;','required':'True',}
    #last_name_attr = {'class': 'form-control', 'placeholder': 'Nom de famille', 'style': 'margin-bottom:10px;','required':'True',}
    email_attr = {'class': 'form-control', 'placeholder': 'Email', 'style': 'margin-bottom:10px;','required':'True',}
    password_attr = {'class': 'form-control', 'placeholder': 'Password', 'style': 'margin-bottom:10px;','required':'True',}
    #birthdate_attr = {'class': 'form-control', 'placeholder': 'Date de naissance' ,'style': 'margin-bottom:10px;','required':'True',}
    place_attr = {'class': 'form-control', 'id':'autocomplete', 'placeholder': 'Ville', 'style': 'margin-bottom:10px;', 'onFocus':'geolocate()','required':'True', }


    #first_name = forms.CharField(label='Prenom', max_length=100, widget=forms.TextInput(attrs=first_name_attr), required=True)
    #last_name = forms.CharField(label='Nom de famille', max_length=100, widget=forms.TextInput(attrs=last_name_attr))
    email = forms.EmailField(label='Email', widget=forms.TextInput(attrs=email_attr), required=True)
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(attrs=password_attr), required=True)
    #birthdate = forms.DateTimeField(label='Date de naissance (jj/mm/aaaa)', widget=forms.TextInput(attrs=birthdate_attr))
    country= forms.CharField(widget=forms.HiddenInput(attrs={'class':'field','id':'country','required':'True',}))
    region= forms.CharField(widget=forms.HiddenInput(attrs={'class':'field','id':'administrative_area_level_1','required':'True',}))
    city= forms.CharField(widget=forms.HiddenInput(attrs={'class':'field','id':'locality','required':'True',}))
    place = forms.CharField(label='Ville', max_length=100, widget=forms.TextInput(attrs=place_attr), required=True)
    accept = forms.BooleanField(label='Charte d\'utilisation', required=True)



    class Meta:
        models= User
        fields=("email","first_name","last_name","birthdate","city",)

    def clean_email(self):
        mail = self.cleaned_data['email']
        try:
            user = User.objects.get(email=mail)
            raise forms.ValidationError(self.error_messages['email_used'],code='email_used',)
        except User.DoesNotExist:
            pass
        return mail

    #Clean function is used to verify correct inputs
    def clean(self):
        country = self.cleaned_data['country']
        region = self.cleaned_data['region']
        city = self.cleaned_data['city']
        #Basical error: a field is not complete
        if not country or not region or not city:
            raise forms.ValidationError(self.error_messages['not_city'],code='not_city',)

        #validate country name
        try:
            db_country = Country.objects.get(name=country)
        except:
            db_country = Country(name=country)
            db_country.save()

        #validate region name
        region = self.cleaned_data['region']
        try:
            db_region = Region.objects.filter(country=db_country).get(name=region)
        except:
            db_region=Region(name=region,country=db_country)
            db_region.save()

        #validate city name
        try:
            db_city = City.objects.filter(region=db_region).get(name=city)
        except:
            db_city = City(name=city, region=db_region)
            db_city.save()
        self.cleaned_data['city']=db_city
        return self.cleaned_data


def create_folder_path(id):
    folder_path = mypath_ZT + "/zatfits/user_models/"+str(id)
    os.makedirs(folder_path)


def subscription(request):
    context = RequestContext(request)
    context_dict = {}
    if request.method == 'POST':
        subscriptionform = SubscriptionForm(request.POST)
        if subscriptionform.is_valid():
            my_password = subscriptionform.cleaned_data.get('password')
            user = User(email=subscriptionform.cleaned_data.get('email'),
                        is_staff=False,
                        is_active=True,
                        date_joined=datetime.datetime.today(),
                        password=my_password,
                        city=subscriptionform.cleaned_data.get('city'))
            user.set_password(my_password)
            user.save()
            user_id = user.id
            #We create the user folder here, this is his private folder
            create_folder_path(user_id)

            usr = authenticate(username=subscriptionform.cleaned_data.get('email'),
                               password=subscriptionform.cleaned_data.get('password'))
            login(request, usr)
            return redirect('dev:index')
        else:
            context_dict['subscriptionform'] = subscriptionform
            return render_to_response('dev/index.html', context_dict, context)
        # inscription
    else:
        return redirect('index.html')


def logout(request):
    # check servers
    svm = ServerManager()
    svm.unassign_user(request.user.id)
    contriblogout(request)
    return redirect('dev:index')


def account(request):
    context = RequestContext(request)
    return render_to_response('dev/account.html', context)


def help(request):
    context = RequestContext(request)
    return render_to_response('dev/help.html', context)


def contact(request):
    context = RequestContext(request)
    return render_to_response('dev/contact.html', context)



def signin(request):

    # add localisation with ip stats like (see django-localisation)
    return render_to_response('dev/index.html', context_dict, context)

def validate(request):
    print('Enter in Validate')
    try:
        print('Request User Model by Validate')
        generate_model.delay(request.user.id, request.POST)
    except Exception as e:
        print(e)
    return redirect('dev:index')
    
def scale(request):
    print('Enter in Validate')
    try:
        print('Scale Test')
        scaleTest.delay(request.user.id, request.POST)
    except Exception as e:
        print(e)
    return redirect('dev:index')

def fittingScript(request):
    print('Enter in Fitting')
    try:
        print('Scale Test')
        fittingProcessus.delay(request.user.id, request.POST)
    except Exception as e:
        print(e)
    return redirect('dev:fitting')

def index(request):
    context = RequestContext(request)
    context_dict = {'subscriptionform': SubscriptionForm(), 'loginform': LoginForm()}
    return render_to_response('dev/index.html', context_dict, context)

def fitting(request):
    context = RequestContext(request)
    context_dict = {}
    return render_to_response('dev/fitting.html', context_dict, context)

def model(request):
    context = RequestContext(request)
    context_dict = {}
    return render_to_response('dev/model.html', context_dict, context)

def places(request):
    context = RequestContext(request)
    context_dict = {}
    return render_to_response('dev/Placetest.html', context_dict, context)
