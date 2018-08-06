import ipywidgets as widgets
import matplotlib.pyplot as plt

from xnatio.data import Data


class SubjectData(Data):

    def __init__(self, options=None):
        """
            Initializes the object

            Parameters
            ----------
            options:  dict
                a dict of options

                "keys": list
                    a list of strings used to determine which properties of objects in arrays can be used to determine a key for that object
                    default: ["field", "names"]

                "id_field": string
                    the the field name of the subject that contains its unique identifier
                    default: "ID" (this is what is used in CNDA)

                "add_data_mode": "merge" | "replace" | "keep" | "append"
                    the mode for adding subject data
                    "merge":
                        if the added subject id matches an existing subject id, merge the two together
                    "replace":
                        if the added subject id matches an existing subject id, replace the old with the new
                    "keep":
                        if the added subject id matches an existing subject id, keep the old and disregard the new
                    "append":
                        just append the subject to the data -- even if there is a matching subject
                    default: "merge"

                "merge_priority": "old" | "new"
                    if there is a conflict when merging subject data together, keep either the old or new data

            Returns
            -------
            SubjectData
                The SubjectData object

        """

        self.subjectGroups = []
        self.groupsDisplayContainer = widgets.VBox()
        self.groupTitleDisplayContainer = widgets.VBox()

        defaults = {
            "id_field": "ID",
            "add_data_mode": "merge",
            "merge_priority": "new"
        }

        if isinstance(options, dict):
            defaults.update(options)

        Data.__init__(self, [], defaults)

    def add_subject(self, subject, options=None):
        """
            Adds new subject to the data

            Parameters
            ----------
            subject: dict
                a dict object representing the subject and its contained data

            options: dict
                optionally provide options that will be applied only to this operation
                "keys": list
                    a list of strings used to determine which properties of objects in arrays can be used to determine a key for that object
                    default: ["field", "names"]

                "id_field": string
                    the the field name of the subject that contains its unique identifier
                    default: "ID" (this is what is used in CNDA)

                "add_data_mode": "merge" | "replace" | "keep" | "append"
                    the mode for adding subject data
                    "merge":
                        if the added subject id matches an existing subject id, merge the two together
                    "replace":
                        if the added subject id matches an existing subject id, replace the old with the new
                    "keep":
                        if the added subject id matches an existing subject id, keep the old and disregard the new
                    "append":
                        just append the subject to the data -- even if there is a matching subject
                    default: "merge"

                "merge_priority": "old" | "new"
                    if there is a conflict when merging subject data together, keep either the old or new data
            Return
            ------
            None


        """

        localOptions = {}
        localOptions.update(self.options)
        if isinstance(options, dict):
            for key, value in options.items():
                localOptions[key] = value

        if not isinstance(subject, dict):
            raise Exception("Subject must be of type dict")

        mode = localOptions["add_data_mode"]

        if mode == "append":
            self.data.append(subject)
        else:
            try:
                newSubjectId = subject[localOptions["id_field"]]
            except:
                raise Exception(
                    "Subject does not contain required id field parameter '" + localOptions['id_field'] + "'")
            else:
                if mode in {"replace", "keep"}:
                    for i in range(len(self.data)):
                        oldSubject = self.data[i]
                        oldSubjectId = oldSubject[self.options["id_field"]]
                        if newSubjectId == oldSubjectId:
                            if mode == "replace":
                                self.data[i] = subject
                            return
                    # subject not in array
                    self.data.append(subject)
                    return
                else:
                    # default case: merge
                    mergePriority = localOptions["merge_priority"]
                    for i in range(len(self.data)):
                        oldSubject = self.data[i]
                        oldSubjectId = oldSubject[self.options["id_field"]]
                        if newSubjectId == oldSubjectId:
                            def merge(new, old):
                                for key, value in new.items():
                                    #                                     print(key)
                                    try:
                                        oldValue = old[key]
                                    except:
                                        # the new key didn't previously exist, so add it
                                        old[key] = value
                                    else:
                                        if isinstance(value, list) and isinstance(oldValue, list):
                                            old[key] = oldValue + value
                                        elif isinstance(value, dict) and isinstance(oldValue, dict):
                                            old[key] = merge(value, oldValue)
                                        else:
                                            if not mergePriority == "old":
                                                old[key] = value
                                return old

                            self.data[i] = merge(subject, oldSubject)
                            return

                    # if the subject isn't in the array
                    self.data.append(subject)
                    return

    def add_subject_group(self, subjects, title=None, options=None):
        """
            Creates a new group from a list of subject ids

            Parameters
            ----------

            subjects: list
                a list of subject ids

            title: string (optional)
                a title for the group.
                if not given, the title will be "Group {number}"

            Returns
            -------
             list [[string:Any]]
                A list of all subject groups

        """
        idField = self.options["id_field"]
        try:
            idField = options["id_field"]
        except:
            pass
        filterGroups = {idField: subjects}
        return self.add_group(filterGroups, title)

    def add_group(self, filterGroups, title=None):
        """
            Adds a new subject groups

            Parameters
            ----------

            filterGroups: dict [string:[Any]]
                a dict where the key is the name of the parameter and the value is a list of acceptable values
                for a subject to be in this group, it must satisfy all of the parameters
                ex:
                {
                    "gender":["Male", "Other"]
                }

            title: string (optional)
                a title for the group.
                if not given, the title will be "Group {number}"

            Returns
            -------
            list [[string:Any]]
                A list of all subject groups

        """

        def filterGroupsDescription(filterGroups, delim="; "):
            string = ""
            count = 0
            for key, values in filterGroups.items():
                count += 1
                string += key + ": "
                for i in range(len(values)):
                    if not i == 0:
                        string += ", "
                    string += values[i]
                if not count == len(filterGroups):
                    string += delim
            return string

        if title == None:
            title = "Group " + str(len(self.subjectGroups))

        newSubjectGroup = {"title": title, "filterGroups": filterGroups,
                           "subjects": SubjectData.subjects_in_filter_groups(self.data, filterGroups)}
        self.subjectGroups.append(newSubjectGroup)

        newGroupLabel = widgets.HTML(value="<b>" + newSubjectGroup["title"] + ":</b><br>&emsp;" +
                                           str(len(newSubjectGroup["subjects"])) + " subjects" +
                                           ("<br>&emsp;" + filterGroupsDescription(newSubjectGroup["filterGroups"],
                                                                                   delim="<br>&emsp;")
                                            if len(newSubjectGroup["filterGroups"]) > 0
                                            else ""))

        groupTitleDisplayContainerChildren = self.groupTitleDisplayContainer.children
        groupTitleDisplayContainerChildren += (newGroupLabel,)
        self.groupTitleDisplayContainer.children = groupTitleDisplayContainerChildren

        checkboxes = []

        # TODO:: Minor optimization, but this doesn't have to regenerate every single checkbox, it only has to add the new one
        for group in self.subjectGroups:
            title = group["title"] + " (" + str(len(group["subjects"])) + " subjects" + (
                "; " + filterGroupsDescription(group["filterGroups"]) if len(group["filterGroups"]) > 0 else "") + ")"

            checkbox = widgets.Checkbox(description=title,
                                        value=True,
                                        disabled=False,
                                        layout=widgets.Layout(width='97%', height='40px'))
            checkboxes.append(checkbox)

        if (self.groupsDisplayContainer == None):
            self.groupsDisplayContainer = widgets.VBox()

        self.groupsDisplayContainer.children = checkboxes

        return self.subjectGroups

    def subjects_in_filter_groups(subjects, filterGroups):
        """
            Static method that returns a list of subjects (not just id's) that satisfy the filterGroups

            Parameters
            ----------

            subjects: list [[string:Any]]
                a list of subjects to be filtered from

            filterGroups: dict [string:[Any]]
                a dict where the key is the name of the parameter and the value is a list of acceptable values
                for a subject to be in this group, it must satisfy all of the parameters
                ex:
                {
                    "gender":["Male", "Other"]
                }

        """

        def subjectInKeyValues(subject, key, values):
            if (len(values) > 0):
                for value in values:
                    val = subject[key]
                    if val == "":
                        val = "no value"
                    if val == value:
                        return True
                return False
            else:
                return True

        def subjectInGroups(subject, groups):
            for key, values in groups.items():
                if isinstance(values, list):
                    if not subjectInKeyValues(subject, key, values):
                        return False
                else:
                    return subject[key] == values
            return True

        filteredSubjects = []
        if len(filterGroups) > 0:
            for subject in subjects:
                if subjectInGroups(subject, filterGroups):
                    filteredSubjects.append(subject)

        return filteredSubjects

    def add_groups_ui(self):
        """
            Returns the UI for creating new groups

            Returns
            -------
            widgets.VBox
                a widget containing the UI

        """

        def getGroupContainer(group):
            groupContainer = widgets.VBox()
            children = []
            for key, value in group.items():
                checkbox = widgets.Checkbox(description=key + " (" + str(value) + ")",
                                            value=False,
                                            disabled=False,
                                            )
                children.append(checkbox)
            ignoreCheckbox = widgets.Checkbox(description="Ignore these parameters", value=False, disabled=False)
            children.append(ignoreCheckbox)

            groupContainer.children = children

            out = widgets.Output()
            with out:
                labels = []
                values = []
                for key, value in group.items():
                    labels.append(key)
                    values.append(value)

                plt.pie(x=values, labels=labels)
                plt.show()

            return widgets.HBox(children=[groupContainer, out])

        def getGroupsContainer(groups):
            groupsContainer = widgets.Accordion()
            children = []
            for key, value in groups.items():
                groupContainer = getGroupContainer(value)
                groupsContainer.set_title(len(children), key)
                children.append(groupContainer)

            groupsContainer.children = children
            return groupsContainer

        groups = {}
        toDelete = []
        for subject in self.data:
            for field, group in subject.items():
                if not (field == "ID" or field == "label" or field == "URI" or isinstance(group, list) or isinstance(
                        group, dict)):
                    if (group == ""):
                        group = "no value"
                    try:
                        num = float(group)
                    #                         print(field + ": " + group)
                    except:
                        try:
                            groups[field][group] += 1
                        except:
                            try:
                                groups[field][group] = 1
                            except:
                                try:
                                    groups[field] = {}
                                    groups[field][group] = 1
                                except:
                                    pass

        for fieldId, field in groups.items():
            keyCount = 0
            count = 0
            for group, value in field.items():
                if not group == "no value":
                    keyCount += 1
                    count += value

            if 2 * keyCount > count or keyCount <= 1:
                toDelete.append(fieldId)

        for fieldId in toDelete:
            del groups[fieldId]

        #         print(groups)

        filteredSubjects = {}

        groupsContainer = getGroupsContainer(groups)
        recalculateButton = widgets.Button(description="Create New Group")
        groupTitleText = widgets.Text(value="Group " + str(len(self.subjectGroups)))
        recalculateContainer = widgets.HBox(children=[groupTitleText, recalculateButton])

        #         self.groupTitleDisplayContainer = widgets.VBox()

        def recalculateGroups(event):
            filterGroups = {}  # field: [allowedGroup1, allowedGroup2]
            for i in range(len(groups)):
                if not groupsContainer.children[i].children[0].children[-1].value:
                    potentialKeys = []

                    for checkbox in groupsContainer.children[i].children[0].children[0:-1]:
                        if not checkbox.description == "Ignore":
                            if (checkbox.value):
                                keyEndIndex = checkbox.description.index(" (")
                                key = checkbox.description[0:keyEndIndex]

                                potentialKeys.append(key)
                    if len(potentialKeys) > 0:
                        filterGroups[groupsContainer._titles[str(i)]] = potentialKeys

            filteredSubjects = SubjectData.subjects_in_filter_groups(self.data, filterGroups)
            #             newSubjectGroup = {"title": groupTitleText.value, "filterGroups": filterGroups, "subjects": filteredSubjects}

            self.add_group(filterGroups, groupTitleText.value)
            groupTitleText.value = "Group " + str(len(self.subjectGroups))

        recalculateButton.on_click(recalculateGroups)
        self.groups_ui = widgets.VBox(children=[groupsContainer, recalculateContainer, self.groupTitleDisplayContainer])
        return self.groups_ui

    def get_selected_subject_ids(self):
        """
            Gets the subject ids that have been selected through groups

            Returns
            -------
            list [[string:Any]]

        """
        subjectIds = []
        for i in range(len(self.groupsDisplayContainer.children)):
            checkbox = self.groupsDisplayContainer.children[i]
            if checkbox.value == True:
                for subject in self.subjectGroups[i]["subjects"]:
                    subjectId = subject[self.options["id_field"]]
                    if not subjectId in subjectIds:
                        subjectIds.append(subjectId)

        return subjectIds

    def select_groups_ui(self):
        return self.groupsDisplayContainer

    def get_data(self, options=None):
        # todo: test this method

        """
           Aggregates and returns data from selected subjects

           Flattens out the heirarchal data by combining like data into points using their least common ancestor

           Parameters
           ----------
           options: dict
               Options for the aggregation

               "format": "list" | "points"
                   the format of the data to be returned
                   list returns a dict of labelled lists of data
                   points returns a list of labelled dict data points
                   default: "points"

            Returns
            -------
            list or dict
                (see options > "format")

        """


        localOptions = {}
        localOptions.update(self.options)
        if isinstance(options, dict):
            localOptions.update(options)


        subjectIds = self.get_selected_subject_ids()

        allData = self.data

        idField = localOptions['id_field']

        self.data = [x for x in allData if x[idField] in subjectIds] #filter the selected subjects

        out = Data.get_data(self, options)

        self.data = allData

        return out

