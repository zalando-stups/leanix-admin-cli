list_tag_groups = '''
{
  listTagGroups: allTagGroups {
    edges {
      node {
        id
        name
        shortName
        description
        mode
        restrictToFactSheetTypes
        tags {
          edges {
            node {
              id
              name
              description
              color
              status
            }
          }
        }
      }
    }
  }
}
'''

create_tag_group = '''
mutation ($name: String!,
          $mode:TagGroupModeEnum!,
          $restrictToFactSheetTypes: [FactSheetType!]!,
          $shortName: String,
          $description: String) {
  createTagGroup(
    name: $name,
    mode: $mode, 
    restrictToFactSheetTypes: $restrictToFactSheetTypes,
    shortName: $shortName,
    description: $description
  ) {
    id
  }
}
'''

update_tag_group = '''
mutation ($id: ID!,
          $patches: [Patch]!) {
  updateTagGroup(
    id: $id,
    patches: $patches
  ) {
    id
  }
}
'''

delete_tag_group = '''
mutation ($id: ID!) {
  deleteTagGroup (id: $id){
    id
  }
}
'''
