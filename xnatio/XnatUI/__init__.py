import requests
import grequests
import ipywidgets as widgets
import json
import getpass
import traceback

from xnatio import SubjectData


class IncorrectLoginException(Exception):
    pass


class XnatUI:
    def __init__(self, server, options=None):
        self.JESSIONID = None
        self.projects = []
        self.projectIds = []
        self.availableProjectsUI = None
        self.fetchedProjectIds = []
        self.subjectData = None
        self.selectedProjectIds = []
        self.experimentTypes = None
        self.experimentContainer = None

        if server[-1] == "/":
            self.server = server[0:-1]
        else:
            self.server = server
        defaults = {
            "force_ssl": True
        }

        if isinstance(options, dict):
            defaults.update(options)
        self.options = defaults

    def __str__(self):
        print("XNAT instance running at " + self.server)

    def get_login(self, username, password):
        """
            Gets and saves the login info

            Parameters
            ----------
            username: str
            password: str

            Returns
            -------
            str
                the session id
        """
        secure = self.options["force_ssl"]
        response = requests.post(self.server + "/data/JSESSIONID",
                                 auth=requests.auth.HTTPBasicAuth(username, password),
                                 verify=secure)

        #         print(vars(response))
        if (response.status_code == 200):
            cookieString = response.headers["Set-Cookie"]
            indexFirst = cookieString.index("JSESSIONID=") + 11
            indexLast = cookieString.index(";", indexFirst)
            self.JSESSIONID = cookieString[indexFirst:indexLast]
            return self.JSESSIONID
        else:
            raise IncorrectLoginException("Username/Password combination incorrect")

    def display_login_ui(self):
        """
            Displays the login UI

            Returns
            -------
            None
        """
        username = input("Username: ")
        password = getpass.getpass("Password: ")

        try:
            return self.get_login(username, password)
            print("Success")
        except IncorrectLoginException:
            #             traceback.print_exc()
            # if login fails, try again
            return self.display_login_ui()

    def get_available_projects(self):
        """
            Fetches then saves the available projects

            Returns
            -------
            list
                the IDs of the available projects
        """
        if (not self.projectIds == None) and len(self.projectIds) > 0:
            return self.projectIds

        if self.JSESSIONID == None:
            raise Exception(
                "Must login first before calling this method (call display_login_ui() or get_login(username, password))")
        projectsResponse = requests.get(self.server + "/data/projects",
                                        headers={"Cookie": "JSESSIONID=" + self.JSESSIONID},
                                        verify=self.options["force_ssl"])
        try:
            assert projectsResponse.status_code == 200
            projects = projectsResponse.json()["ResultSet"]["Result"]
        except:
            raise Exception("API returned error")
        else:
            projectIds = []

            for project in projects:
                projectIds.append(project["ID"])

            self.projects = projects
            self.projectIds = sorted(projectIds, key=lambda s: s.lower())
            return self.projectIds

    def get_available_projects_ui(self):
        """
            Gets the available projects then returns the UI for selecting them

            Returns
            -------
            ipywidget
        """
        # possible improvement: Able to add through regex
        if self.availableProjectsUI == None:
            projectIds = self.get_available_projects()
            self.selectedProjectIds = []

            self.availableProjectsUI = widgets.VBox()
            addedContainer = widgets.VBox()
            addContainer = widgets.HBox()

            self.availableProjectsUI.children = (addedContainer, addContainer)

            dd = widgets.Dropdown(options=projectIds)
            addButton = widgets.Button(description="Add")

            def remove(projectId, b):
                self.availableProjectsUI.children[0].children = tuple(
                    project
                    for project in self.availableProjectsUI.children[0].children
                    if not project.children[1].value == projectId
                )
                try:
                    self.selectedProjectIds.remove(projectId)
                except:
                    pass

            def add(b):
                # add to the data
                currentId = dd.value
                if not currentId in self.selectedProjectIds:
                    self.selectedProjectIds.append(currentId)

                    # add to the UI

                    title = widgets.HTML(value=currentId)
                    button = widgets.Button(description="Remove")

                    button.on_click(lambda b: remove(currentId, b))

                    childrenArray = self.availableProjectsUI.children[0].children
                    childrenArray = childrenArray + (widgets.HBox(children=[
                        button, title
                    ]),)

                    self.availableProjectsUI.children[0].children = childrenArray

            addButton.on_click(add)
            addContainer.children = (dd, addButton)

            return self.availableProjectsUI
        else:
            return self.availableProjectsUI

    def select_project(self, project):
        """
            Selects a project, given the ID

            Parameters
            ----------
            project: str
                the ID of the project to be selected

            Returns
            -------
            list
                a list of the IDs of all selected projects
        """
        self.selectedProjectIds.append(project)

        self.experimentTypes = None

        return self.selectedProjectIds

    def select_projects(self, projects):
        """
            Selects projects, given a list of IDs

            Parameters
            ----------
            projecto: list
                the list of the IDs of the projects to be selected

            Returns
            -------
            list
                a list of the IDs of all selected projects
        """
        self.selectedProjectIds += projects

        self.experimentTypes = None

        return self.selectedProjectIds

    def get_selected_projects(self):
        """
            Returns the list of selected project IDs

            Returns
            -------
            list
        """
        return self.selectedProjectIds

    def fetch_subjects(self, options=None):
        """
            Fetches (if not fetched already) subjectData

            Returns
            -------
            SubjectData
        """

        secure = self.options["force_ssl"]
        try:
            secure = options["force_ssl"]
        except:
            pass

        projectsToGet = [project for project in self.selectedProjectIds if not project in self.fetchedProjectIds]
        requests = (grequests.get(self.server + "/data/projects/" + project + "/subjects",
                                  headers={"Cookie": "JSESSIONID=" + self.JSESSIONID},
                                  params={
                                      "format": "json",
                                      "columns": """age,birth_weight,dob,education,educationDesc,
                                       ethnicity,gender,gestational_age,group,handedness,
                                       height,insert_date,insert_user,last_modified,pi_firstname,
                                       pi_lastname,post_menstrual_age,race,ses,src,weight,yob"""
                                  },
                                  verify=secure) for project in projectsToGet)

        results = grequests.map(requests)

        if self.subjectData == None:
            self.subjectData = SubjectData({"id_field": "ID"})

        for count, result in enumerate(results):
            if result.status_code == 200:
                try:
                    subjects = result.json()["ResultSet"]["Result"]
                except:
                    traceback.print_exc()
                    pass
                else:
                    self.fetchedProjectIds.append(projectsToGet[count])
                    for i in range(len(subjects)):
                        subjects[i]["project"] = projectsToGet[count]
                        subjects[i]["experiments"] = {}
                        self.subjectData.add_subject(subjects[i])

        return self.subjectData

    def get_available_experiments(self, options=None):
        """
            Gets the types of experiments that are available

            Returns
            -------
            dict [str:[str:[str]]]
        """

        if not self.experimentTypes == None:
            return self.experimentTypes

        secure = self.options["force_ssl"]
        try:
            secure = options["force_ssl"]
        except:
            pass

        experimentsRequests = (grequests.get(self.server + "/data/projects/" + project + "/experiments",
                                             headers={"Cookie": "JSESSIONID=" + self.JSESSIONID},
                                             params={
                                                 "format": "json",
                                                 "columns": "xsiType,label,subject_ID,ID"
                                             },
                                             verify=secure) for project in self.selectedProjectIds)
        experimentsResults = grequests.map(experimentsRequests)

        groupIds = {}
        expGroupCount = {}
        experimentTypes = {}

        for result in experimentsResults:
            try:
                exp = result.json()["ResultSet"]["Result"]
            except:
                print("You are not logged in")
            else:
                for e in exp:
                    try:
                        experimentTypes[e["xsiType"]][e["subject_ID"]].append(e["ID"])
                    except:
                        try:
                            experimentTypes[e["xsiType"]][e["subject_ID"]] = [e["ID"]]
                        except:
                            experimentTypes[e["xsiType"]] = {
                                e["subject_ID"]: [e["ID"]]
                            }
        #                     for group, subs in groupIds.items():
        #                         subId = e["subject_ID"]
        #                         expType = e["xsiType"]
        #                         if subId in subs:
        #                             try:
        #                                 expGroupCount[expType][group] += 1
        #                             except:
        #                                 try:
        #                                     expGroupCount[expType][group] = 1
        #                                 except:
        #                                     expGroupCount[expType] = {group: 1}

        self.experimentTypes = experimentTypes
        return self.experimentTypes

    def get_available_experiments_ui(self):
        """
            Gets the UI for selecting experiments

            Returns
            -------
            ipywidget
        """
        if self.experimentTypes == None or len(self.experimentTypes) == 0:
            self.get_available_experiments()

        groupIds = {}
        for subjectGroup in self.subjectData.subjectGroups:
            groupIds[subjectGroup["title"]] = []
            for subject in subjectGroup["subjects"]:
                groupIds[subjectGroup["title"]].append(subject["ID"])

        expGroupCount = {}

        for expId, subjects in self.experimentTypes.items():
            expGroupCount[expId] = {}
            for groupId, subjectIds in groupIds.items():
                expGroupCount[expId][groupId] = 0;
                for subjectId in subjectIds:
                    try:
                        count = len(self.experimentTypes[expId][subjectId])
                    except:
                        pass
                    else:
                        expGroupCount[expId][groupId] += count

        options = []
        for xsi, subjectId in self.experimentTypes.items():
            title = xsi + " ("
            for subjectGroup in self.subjectData.subjectGroups:
                count = 0
                group = subjectGroup["title"]
                try:
                    count = expGroupCount[xsi][group]
                except:
                    pass
                title += str(group) + ": " + str(count) + " experiments; "
            options.append(title[0:-2] + ")")

        experimentButtons = widgets.Dropdown(options=sorted(options),

                                             description="Data Types: ",
                                             disabled=False,
                                             value=None)
        self.experimentContainer = widgets.HBox()
        experimentGoButton = widgets.Button(description='Go')
        experimentGoButton.on_click(self.get_experiment_from_ui)

        self.experimentContainer.children = [experimentButtons, experimentGoButton]

        return self.experimentContainer

    def get_experiment_from_ui(self, event=None):
        """
            Gets the experiment that is currently selected

            Returns
            -------
            None
        """
        codeStr = self.experimentContainer.children[0].value
        endIndex = codeStr.index(" (")
        experimentCode = codeStr[0:endIndex]
        return self.get_experiment(experimentCode, self.subjectData.get_selected_subject_ids())

    def get_experiment(self, experimentCode, subjectIds=None, options=None):
        """
            Gets a specific experiment

            Parameters
            ----------
            experimentCode: str
                the xsi:type of the experiments to get

            subjectIds: list (optional)
                a list of the IDs of subjects to get

            Returns
            -------
            None
        """

        secure = self.options["force_ssl"]
        try:
            secure = options["force_ssl"]
        except:
            pass

        experiments = []
        experimentSubjects = self.experimentTypes[experimentCode]
        if subjectIds == None:
            subjectIds = self.subjectData.get_selected_subject_ids()
        for subject in subjectIds:
            try:
                experiments += experimentSubjects[subject]
            except:
                pass

        requests = [grequests.get(self.server + "/data/experiments/" + exp,
                                  headers={"Cookie": "JSESSIONID=" + self.JSESSIONID},
                                  params={"format": "json"},
                                  verify=secure) for exp in experiments]

        def exceptionHandler(req, exc):
            print(exc)

        result = grequests.map(requests, exception_handler=exceptionHandler)

        #     print("woo")
        #     print(result)
        #     print(result[0]._content)

        for exResult in result:
            try:
                exDict = json.loads(exResult._content.decode('utf-8'))['items'][0]
            except:
                pass
            else:
                exSubjectId = exDict['data_fields']['subject_ID']
                self.subjectData.add_subject({"ID": exSubjectId, "experiments": {exDict['meta']['xsi:type']: [exDict]}},
                                             options={'add_data_mode': 'merge', 'merge_priority': 'old'})

        print("Done getting experiments")

# temp
# xnat = XnatUI("https://cnda-dev-aidan1.nrg.mir", {"force_ssl":False})
# # xnat.display_login_ui(); # ';' will suppress output
# xnat.get_login('aidan','')
# # xnat.get_available_projects_ui()
# xnat.select_project('DIAN_011')
# xnat.fetch_subjects().calculate_groups()
# xnat.fetch_subjects().add_group({'ID':'CNDA0516'}, "CNDA0516")
# xnat.get_available_experiments_ui()
# # xnat.subjectData.groupsDisplayContainer
# # subjects = xnat.subjectData.add_group({'insert_user':['dan']})[-1]["subjects"]
# # subjectIds = []
# # for subject in subjects:
# #     subjectIds.append(subject["ID"])
# # print(subjectIds)
# # xnat.get_available_experiments()
# xnat.get_available_experiments_ui()

