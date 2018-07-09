import graphene

import announcements.schema


class Queries(
    announcements.schema.Query,
    graphene.ObjectType
):
    pass

schema = graphene.Schema(query=Queries)
