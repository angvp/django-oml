class ModeratedModelManager(object):

    def moderated(self):
        return self.filter(status=False)
