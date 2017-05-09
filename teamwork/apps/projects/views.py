from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect)
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User

from teamwork.apps.core.models import *
from teamwork.apps.courses.models import *

from .forms import *
from .models import *

import json


def _projects(request, projects):
    """
    Private method that will be used for paginator once I figure out how to get it working.
    """
    page = request.GET.get('page')

    
    # Populate with page name and title
    page_name = "My Projects"
    page_description = "Projects created by " + request.user.username
    title = "My Projects"


    return render(request, 'projects/view_projects.html', {'page_name': page_name,
        'page_description': page_description, 'title' : title,
        'projects': projects})


@login_required
def view_projects(request):
    """
    Public method that takes a request, retrieves all Project objects from the model,
    then calls _projects to render the request to template view_projects.html
    """
    my_projects = Project.get_my_projects(request.user)
    my_created = Project.get_created_projects(request.user)
    projects = my_projects | my_created
    projects = list(set(projects))

    return _projects(request, projects)



def view_one_project(request, slug):
    """
    Public method that takes a request and a slug, retrieves the Project object
    from the model with given project slug.  Renders projects/view_project.html

    Passing status check unit test in test_views.py.
    """

    project = get_object_or_404(Project, slug=slug)
    updates = project.get_updates()

    # Get the course given a project wow ethan great job keep it up.
    course = Course.objects.get(projects=project)


    # Populate with project name and tagline
    page_name = project.title or "Project"
    page_description = project.tagline or "Tagline"
    title = project.title or "Project"

    return render(request, 'projects/view_project.html', {'page_name': page_name,
        'page_description': page_description, 'title' : title,
        'project': project, 'updates': updates, 'course' : course})


def select_members(request):
    if request.method == 'POST' and request.is_ajax():
        # Not sure if db save should be handled here or in create_project
        #selected_members_json = request.POST.get('q')

        #print("\n\nDebug: data : " + selected_members_json + "\n\n")

        # Load json user list into a python list of dicts
        #selected_members = json.loads(selected_members_json)

        # selected_members_json = request.POST.getlist("members")
        # print("\n\nDebug: selected_members_json : \n\n")
        # print(selected_members_json)


        return HttpResponse("Form Submitted")

    elif request.method == 'GET' and request.is_ajax():
        # JSON prefers dictionaries over lists.
        data = dict()
        # A list in a dictionary, accessed in select2 ajax
        data['items'] = []
        q = request.GET.get('q')
        if q is not None:
            results = User.objects.filter( 
                Q( first_name__contains = q ) |
                Q( last_name__contains = q ) |
                Q( username__contains = q ) ).order_by( 'username' )
        for u in results:
            data['items'].append({'id': u.username, 'text': u.username})
        return JsonResponse(data)


    return HttpResponse("Failure")

@login_required
def create_project(request):
    """
    Public method that creates a form and renders the request to create_project.html
    """
    # Populate page info with new project headers/title
    page_name = "Create Project"
    page_description = "Post a new project"
    title = "Create Project"
    user_id = request.user.id
    user = Profile.objects.get(user=user_id)
    #enrollment objects containing current user
    enroll = Enrollment.objects.filter(user=request.user)
    #current courses user is in
    cur_courses = Course.objects.filter(enrollment__in=enroll)
    no_postable_classes = False

    my_created_courses = Course.objects.filter(creator=request.user.username)
    #If user is in 0 courses
    if len(enroll) == 0 and len(my_created_courses) == 0:
        #Redirect them to homepage and tell them to join a course
        messages.info(request,
                      'You need to join a course before creating projects!')
        return HttpResponseRedirect('/')

    if len(cur_courses) == len(cur_courses.filter(limit_creation=True)):
        no_postable_classes = True

    if len(enroll) >= 1 and no_postable_classes and not user.isProf:
        #Redirect them to homepage and tell them to join a course
        messages.info(request, 'Professor has disabled Project Creation!')
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        # Not sure if db save should be handled here or in create_project
        #selected_members_json = request.POST.get('q')

        # Load json user list into a python list of dicts
        #selected_members = json.loads(selected_members_json)

        form = ProjectForm(request.user.id, request.POST)
        if form.is_valid():
            # create an object for the input
            project = Project()
            # Project slug
            project.slug = form.cleaned_data.get('slug')
            project.title = form.cleaned_data.get('title')
            project.tagline = form.cleaned_data.get('tagline')
            project.creator = request.user.username
            project.avail_mem = form.cleaned_data.get('accepting')
            project.sponsor = form.cleaned_data.get('sponsor')
            project.resource = form.cleaned_data.get('resource')
            project.weigh_interest = form.cleaned_data.get('weigh_interest') or 0
            project.weigh_know = form.cleaned_data.get('weigh_know') or 0
            project.weigh_learn = form.cleaned_data.get('weigh_learn') or 0

            project.save()


            # Handle desired skills
            desired = form.cleaned_data.get('desired_skills')
            if desired:
                # parse known on ','
                skill_array = desired.split(',')
                for skill in skill_array:
                    stripped_skill = skill.strip()
                    if not (stripped_skill == ""):
                        # check if skill is in Skills table, lower standardizes input
                        if Skills.objects.filter(skill=stripped_skill.lower()):
                            # skill already exists, then pull it up
                            desired_skill = Skills.objects.get(
                                skill=stripped_skill.lower())
                        else:
                            # we have to add the skill to the table
                            desired_skill = Skills.objects.create(
                                skill=stripped_skill.lower())
                            # save the new object
                            desired_skill.save()
                        # This is how we can use the reverse of the relationship
                        # add the skill to the current profile
                        project.desired_skills.add(desired_skill)
                        project.save(
                        )  #taking profile.save() out of these if's and outside lets all the changes be saved at once
                        # This is how we can get all the skills from a user
                    # Project content
            project.content = form.cleaned_data.get('content')

            # Local list of memebers, used to create Membership objects
            # Now not getting this list through the form, because this list is created
            # using select2 javascript.
            members = request.POST.getlist('members')
            print(members)

            project.save()

            in_course = form.cleaned_data.get('course')
            in_course.projects.add(project)

            # loop through the members in the object and make m2m rows for them
            for i in members:
                i_user = User.objects.get(username=i)
                mem_courses = Course.get_my_courses(i_user)
                if in_course in mem_courses:
                    Membership.objects.create(
                        user=i_user, project=project, invite_reason='')

            # if user is not a prof
            if not user.isProf:
                Membership.objects.create(
                    user=user.user, project=project, invite_reason='')

            # we dont have to save again because we do not touch the project object
            # we are doing behind the scenes stuff (waves hand)
            return redirect(view_projects)
    else:
        # Send form for initial project creation
        form = ProjectForm(request.user.id)
    return render(request, 'projects/create_project.html', {'page_name': page_name,
        'page_description': page_description, 'title' : title, 'form': form})


@login_required
def edit_project(request, slug):
    """
    Public method that serves the form allowing a user to edit a project
    Based off courses/views.py/edit_course
    """
    project = get_object_or_404(Project, slug=slug)

    # Populate page info with edit project title/name
    page_name = "Edit Project"
    page_description = "Make changes to " + project.title
    title = "Edit Project"

    # if user is not project owner or they arent in the member list
    if not request.user.username == project.creator and request.user not in project.members.all(
    ):
        #redirect them with a message
        messages.info(request, 'Only Project Owner can edit project!')
        return HttpResponseRedirect('/project/all')

    if request.method == 'POST':
        form = ProjectForm(request.user.id, request.POST)
        if form.is_valid():
            # edit the project object, omitting slug
            project.title = form.cleaned_data.get('title')
            project.tagline = form.cleaned_data.get('tagline')
            project.avail_mem = form.cleaned_data.get('accepting')
            project.sponsor = form.cleaned_data.get('sponsor')
            project.resource = form.cleaned_data.get('resource')
            project.weigh_interest = form.cleaned_data.get('weigh_interest') or 0
            project.weigh_know = form.cleaned_data.get('weigh_know') or 0
            project.weigh_learn = form.cleaned_data.get('weigh_learn') or 0

            project.save()

            members = form.cleaned_data.get('members')

            # Clear all memberships to avoid duplicates.
            memberships = Membership.objects.filter(project=project)
            if memberships is not None: memberships.delete()

            for i in members:
                Membership.objects.create(
                    user=i.user, project=project, invite_reason='')

            # Not sure if view_one_project redirect will work...
            return redirect(view_one_project, project.slug)
    else:
        form = ProjectForm(request.user.id, instance=project)
    return render(request, 'projects/edit_project.html', {'page_name': page_name,
        'page_description': page_description, 'title' : title,
        'form': form, 'project': project})


@login_required
def delete_project(request, slug):
    """
    Delete project method
    """
    project = get_object_or_404(Project, slug=slug)

    ## Do something to check that the current user is the project owner
    # if not request.user.id == project.owner.id:
    #     return redirect(view_one_project, project.slug)
    # else:
    #     project.delete()
    #     return redirect(view_projects)

    project.delete()
    return redirect(view_projects)


@login_required
def post_update(request, slug):
    """
    Post an update for a given project
    """
    project = get_object_or_404(Project, slug=slug)

    if not request.user.username == project.creator and request.user not in project.members.all(
    ):
        #redirect them with a message
        messages.info(request, 'Only current members can post an update for a project!')
        return HttpResponseRedirect('/project/all')

    if request.method == 'POST':
        form = UpdateForm(request.user.id, request.POST)
        if form.is_valid():
            new_update = ProjectUpdate(project=project)
            new_update.update = form.cleaned_data.get('update')
            new_update.update_title = form.cleaned_data.get('update_title')
            new_update.user = request.user
            new_update.save()
            return redirect(view_one_project, project.slug)
    else:
        form = UpdateForm(request.user.id)
    return render(request, 'projects/post_update.html',
                  {'form': form,
                   'project': project})
@login_required
def find_meeting(request, slug):
    """
    Find and store possible meeting time for a given project
    """
    # Gets current project
    project = get_object_or_404(Project, slug=slug)

    # If project already has a list of meeting times, delete it
    if project.meetings is not None: project.meetings.delete()

    # Stores avaliablity in list
    event = project.generate_avail

    # Adds meeting to model
    project.meetings.add(event)
    project.save()


    return render(request, 'projects/view_projects.html',
                  {'projects': projects})
