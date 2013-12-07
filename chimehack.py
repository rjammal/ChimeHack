import sqlite3

# Set up database
connection = sqlite3.connect(':memory:')
c = connection.cursor()


c.execute("""create table garden (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                  Name TEXT NOT NULL, Title TEXT, City TEXT)""")

c.execute("""create table category (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                    Name TEXT, ShortName TEXT)""")

c.execute("""insert into category (Name, ShortName) values
             ('Driving Force or Sense of Mission', 'Driving Force')""") #1
c.execute("""insert into category (Name, ShortName) values
             ('Strong Roots in the Community', 'Community Roots')""") #2
c.execute("""insert into category (Name, ShortName) values
             ('Ability to Connect Across Lines That Divide', 'Cross the Divide')""") #3
c.execute("""insert into category (Name, ShortName) values
             ('Bold Ideas and Bold Action', 'Bold Thinking')""")# 4
c.execute("""insert into category (Name, ShortName) values
             ('Paying it Forward', 'Pay it Forward')""")# 5


c.execute("""create table gardenComments (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                          GardenID INTEGER NOT NULL,
                                          CommenterGardenID INTEGER NOT NULL,
                                          CategoryID INTEGER NOT NULL, 
                                          Comment TEXT NOT NULL,
                                          Created DATETIME NOT NULL, 
                                          FOREIGN KEY (GardenID) REFERENCES garden (ID),
                                          FOREIGN KEY (CommenterGardenID) REFERENCES garden (ID),
                                          FOREIGN KEY (CategoryID) REFERENCES category (ID)
                                          )""")

c.execute("""create table bookmarkedStories (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                             CommentID INTEGER NOT NULL,
                                             BookmarkerID INTEGER NOT NULL, 
                                             BookmarkTimestamp DATETIME, 
                                             FOREIGN KEY (BookmarkerID) REFERENCES garden (ID),
                                             FOREIGN KEY (CommentID) REFERENCES gardenComments (ID))""")



class Garden:

    def __init__(self, name, title, city):
        c.execute("""insert into garden (Name, Title, City)
                     values ('""" + name + "', '" + title + "', '" + city + "')")
        c.execute("select MAX(ID) from garden")
        self.ID = c.fetchall()[0][0]
        self.name = name
        self.title = title
        self.city = city

    def get_ID(self):
        return self.ID
    def get_name(self):
        return self.name
    def get_city(self):
        return self.city

    def addComment(self, commenter_ID, category_ID, comment):
        c.execute("""insert into gardenComments (GardenID, CommenterGardenID, CategoryID, Comment, Created)
                     values (""" + str(self.get_ID()) + ", " + str(commenter_ID) + ", " + str(category_ID) + ", '" + comment + "', datetime('now'))")
    
    def print_all_comments(self):
        c.execute("""select comment.ID, CommenterGarden.Name, category.ShortName, comment.Comment
                     from gardenComments comment JOIN garden CommenterGarden ON comment.CommenterGardenID = CommenterGarden.ID
                                                 JOIN category ON comment.CategoryID = category.ID
                     where comment.GardenID = """ + str(self.get_ID()))
        for row in c.fetchall():
            print(row)

    def get_my_feed(self):
        feed = []
        myID = str(self.get_ID())

        # get discovery 
        c.execute("""select comment.ID, garden.Name, comment.Comment, comment.Created, count(*) Count
                     from gardenComments comment left join bookmarkedStories bookmarks on bookmarks.CommentID = comment.ID
                                                 left join garden on comment.GardenID = garden.ID
                     where bookmarks.BookmarkerID <> """ + myID + """ AND
                           comment.GardenID <> """ + myID + """ AND
                           comment.CommenterGardenID <> """ + myID + """
                     group by garden.Name, comment.Comment, comment.Created
                     order by Count desc""")
        discovery_list = c.fetchall()
        if len(discovery_list) > 0:
            discovery_tuple = discovery_list[0] # for loop is not needed because it will always be only 1 row/tuple in result
            discovery_comment_ID = discovery_tuple[0]
            discovery_garden = discovery_tuple[1]
            discovery_comment = discovery_tuple[2]
            discovery_comment_time = discovery_tuple[3]
            discovery_bookmarked_status = 0
            discovery_without_count = (discovery_comment_ID, discovery_garden, discovery_comment, discovery_comment_time, discovery_bookmarked_status)
            feed.append(discovery_without_count) 

        # get bookmarks and comments about yourself
        c.execute("""select comment.ID, garden.Name, comment.Comment, comment.Created, bookmark.BookmarkerID IS NULL, bookmark.BookmarkTimestamp
                     from gardenComments comment left join BookmarkedStories bookmark ON bookmark.CommentID = comment.ID
                                                 join Garden garden on comment.GardenID = garden.ID
                     where bookmark.BookmarkerID = """ + myID + """ OR
                           comment.GardenID = """ + myID + """
                     order by bookmark.BookmarkTimestamp desc""")
        bookmarked_comments = c.fetchall()
        bookmarked_comments_without_bookmark_timestamp = []
        for comment_tuple in bookmarked_comments:
            comment_ID = comment_tuple[0]
            garden_name = comment_tuple[1]
            comment = comment_tuple[2]
            time = comment_tuple[3]
            bookmarked = comment_tuple[4]
            bookmarked_comments_without_bookmark_timestamp.append((comment_ID, garden_name, comment, time, bookmarked))
        feed.extend(bookmarked_comments_without_bookmark_timestamp)

        feed = remove_duplicates_helper(feed)
        return feed

    def get_garden_section_feed(self, garden_id, category_id):

        feed = []
        myID = str(self.get_ID())
        # show stories I bookmarked first
        c.execute("""select comment.ID, Garden.Name, comment.Comment, comment.Created, 1=1
                     from gardenComments comment join Garden on comment.GardenID = Garden.ID
                                                 join BookmarkedStories bookmark on comment.ID = bookmark.CommentID
                     where Garden.ID = """ + str(garden_id) + """ AND
                           comment.CategoryID = """ + str(category_id) + """ AND
                           bookmark.BookmarkerID = """ + myID)

        feed.extend(c.fetchall())

        # show the rest of the stories
        c.execute("""select comment.ID, Garden.Name, comment.Comment, comment.Created, 1=0
                     from gardenComments comment join Garden on comment.GardenID = Garden.ID
                                                 left join BookmarkedStories bookmark on comment.ID = bookmark.CommentID
                     where Garden.ID = """ + str(garden_id) + """ AND
                           comment.CategoryID = """ + str(category_id) + """ AND
                           (bookmark.BookmarkerID <> """ + myID + """ OR
                            bookmark.BookmarkerID is null)""")

        feed.extend(c.fetchall())

        feed = remove_duplicates_helper(feed)
        return feed

    
    def likeComment(self, commentID):  
        c.execute("""insert into bookmarkedStories (BookmarkerID, CommentID, BookmarkTimestamp)
                     values (""" + str(self.get_ID()) + ', ' + str(commentID) + ", datetime('now'))")


def get_comment_influence(comment_ID):
    c.execute("""select COUNT(*) from bookmarkedStories where ID = """ + str(comment_ID))
    num_bookmarked = c.fetchall()[0][0]
    if num_bookmarked == 0:
        return 1
    elif num_bookmarked < 5:
        return 2
    else:
        return 3

def remove_duplicates_helper(list_with_dupes): 
   seen = {}
   result = []
   for item in list_with_dupes:
       if item in seen:
           continue
       seen[item] = 1
       result.append(item)
   return result

g1 = Garden('Marie Curie', 'Chemist', 'France')
g2 = Garden('Jane Smith', 'Vital Voices Member', 'USA')
g3 = Garden('Michelle Obama', 'First Lady', 'USA')
g4 = Garden('Beyonce', 'Performer', 'USA')
g5 = Garden('Aung San Suu Kyi', 'Politician', 'Myanmar')

        
g3.addComment(g1.get_ID(), 2, "Michelle Obama promotes community farming")#1
g3.addComment(g1.get_ID(), 5, "Michelle serves as a role model for women everywhere")#2
g4.addComment(g2.get_ID(), 3, "Beyonce appeals to a global community to spread her message")#3
g3.addComment(g2.get_ID(), 3, "Michelle fights for LGBT rights")#4
g3.addComment(g1.get_ID(), 2, "Michelle is working to wipe out childhood obesity")#5
g3.addComment(g5.get_ID(), 2, "Michelle is family oriented")#6
g2.addComment(g4.get_ID(), 1, "Jane is one of the most driven people I know" )#8


#g1.addComment(g2.get_ID(), 4, "Kate writing a story about Rosemary")#4


g1.likeComment(5)
g2.likeComment(1)# Rosalind likes comment 1
g2.likeComment(5)
g3.likeComment(5)
g4.likeComment(5)
g5.likeComment(5)
g3.likeComment(3)
g5.likeComment(7)

#print(get_comment_influence(1))

##c.execute("""select * from gardenComments""")
##for row in c.fetchall():
##    print(row)

#c.execute("""select * from bookmarkedStories""")
#print(c.fetchall())
print('Michelle Feed:', g3.get_my_feed())
print('Michelle Garden Section 2 as viewed by Marie Curie: ', g1.get_garden_section_feed(3, 2))


