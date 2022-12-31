import datetime
import re
import sys

from flask import Flask
from flask import render_template
from flask import render_template_string
from flask import request
from flask import abort
from flask import make_response
from flask import redirect

import random
import string

from flask_pymongo import PyMongo

from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import uuid

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'notes'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/notes'

mongo = PyMongo(app)

colors = ["LightSeaGreen", "DarkOrange", "Orange", "SlateBlue", "SkyBlue", "ForestGreen",
            "Gold", "MediumAquaMarine", "YellowGreen", "OrangeRed", "BlueViolet", "DeepSkyBlue"]

def enhance_title(ss, title):
    if ss != None and len(ss) >= 3:
        ntitle = ""
        ltitle = title.lower()
        checkforhref = True
        found = ltitle.find(ss.lower())
        offset = 0
        while found >= 0:
            endfound = found+len(ss)-1
            while found >= 0 and ltitle[found] not in [' ', '.', '\t', '\n', '(', '[', '{', '$', '\'', '"', '/', '>']:
                found -= 1
            found += 1
            while endfound < len(ltitle) and ltitle[endfound] not in \
                [' ', '.', '\t', '\n', ',', '!', '?', '(', '%', '[', ')', ']', '}', '\'', '"', '<', '/']:
                endfound += 1
            ntitle += title[offset:found]
            # https://www.w3schools.com/colors/colors_shades.asp
            ntitle += "<label style=\"background-color:#F0F0F0\">" + title[found:endfound] + "</label>"
            offset = endfound
            found = ltitle.find(ss.lower(), offset, len(ltitle))
        ntitle += title[offset:len(ltitle)]
        title = ntitle
    return title


def enhance_text(ss, text):
    etext = "" #enhanced text
    done = False
    startfrom = 0
    hrefs = []
    while not done:
        index = text.find("https://", startfrom)
        if index == -1:
            index = text.find("http://", startfrom)
        if index == -1:
            etext += text[startfrom:]
            done = True
        else:
            ci = index
            lastchar = ''
            while ci < len(text) and text[ci] not in string.whitespace:
                lastchar = text[ci]
                ci += 1
            if lastchar in ['.',',']:
                ci -= 1
            if index != 0:
                href_start = len(etext + text[startfrom:index])
                href_end = len(etext + text[startfrom:index] + "<a href=\"" + text[index:ci] + "\">")
                hrefs.append((href_start, href_end))
                etext += text[startfrom:index] + "<a href=\"" + text[index:ci] + "\">" + text[index:ci] + "</a>"
            else:    
                href_start = 0
                href_end = len("<a href=\"" + text[index:ci] + "\">")
                hrefs.append((href_start, href_end))
                etext += "<a href=\"" + text[index:ci] + "\">" + text[index:ci] + "</a>"
            startfrom = ci
    #print("hrefs: " + str(hrefs))
    if ss != None and len(ss) >= 3:
        ntext = ""
        ltext = etext.lower()
        checkforhref = True
        found = ltext.find(ss.lower())
        while checkforhref and found >= 0:
            inhref = False
            for hr in hrefs:
                if found > hr[0] and found < hr[1]:
                    inhref = True
                    found = ltext.find(ss.lower(), hr[1], len(ltext))
                    break
            if not inhref:
                checkforhref = False
        offset = 0
        while found >= 0:
            endfound = found+len(ss)-1
            while found >= 0 and ltext[found] not in [' ', '.', '\t', '\n', '(', '[', '{', '$', '\'', '"', '/', '>']:
                found -= 1
            found += 1
            while endfound < len(ltext) and ltext[endfound] not in \
                [' ', '.', '\t', '\n', ',', '!', '?', '(', '%', '[', ')', ']', '}', '\'', '"', '<', '/']:
                endfound += 1
            ntext += etext[offset:found]
            # https://www.w3schools.com/colors/colors_shades.asp
            ntext += "<label style=\"background-color:#F0F0F0\">" + etext[found:endfound] + "</label>"
            offset = endfound
            found = ltext.find(ss.lower(), offset, len(ltext))
            checkforhref = True
            while checkforhref and found >= 0:
                inhref = False
                for hr in hrefs:
                    if found > hr[0] and found < hr[1]:
                        inhref = True
                        found = ltext.find(ss.lower(), hr[1], len(ltext))
                        if found > 0:
                            print("found in href so now found is: '" + ltext[found:found+10] + "'")
                        break
                if not inhref:
                    checkforhref = False
        ntext += etext[offset:len(ltext)]
        #print("ncontent = " + ncontent)
        etext = ntext
    etext = re.sub(r'\r\n', '<br>', etext)
    etext = re.sub(r'\n', '<br>', etext) # in case lines are only terminated by \n
    etext = re.sub(r'\t', '&nbsp;&nbsp;&nbsp;&nbsp;', etext)
    return etext



@app.route("/edit", methods=["POST"])
def notes_edit():
    user = request.cookies.get('user')
    if not cookie_good(user):
        return(make_response("not allowed"))
    notes = mongo.db.notes
    colori = random.randint(0, len(colors)-1)
    if 'ef_skip' in request.form:
        # if ef_skip is defined, this is a request for the edit form containing the note to edit
        ef_skip = int(request.form['ef_skip'])
        if 'ef_ss' in request.form:
            ef_ss = request.form['ef_ss']
        if 'ef_id' in request.form:
            ef_id = request.form['ef_id']
        if len(ef_id) > 0:
            notes = mongo.db.notes
            doc = notes.find_one({"_id": ObjectId(ef_id)})
            if doc:
                resp = render_template('edit.html', 
                        ncolor=colors[colori], _id=str(doc['_id']), title=doc['title'], body=doc['body'],
                        skip=ef_skip, ss=ef_ss)
            else:
                resp = make_response("the note does not exist")
        else:
            resp = make_response("bad id")
        return resp
    #print(request.form)
    title = ""
    body = ""
    datestr = ""
    tzoffset = 0
    delete_note = False
    if ('edit_or_delete' in request.form and request.form['edit_or_delete'] == "delete"):
        delete_note = True
    if (request.form['notebody'] != None and len(request.form['notebody']) > 5000):
        return "form problem"
    else:
        body = request.form['notebody']
    if (request.form['notetitle'] != None and len(request.form['notetitle']) > 500):
        return "form problem"
    else:
        title = request.form['notetitle']
    if 'tzoffset' in request.form:
        tzoffset = int(request.form['tzoffset'])
    if 'skip' in request.form:
        skip = int(request.form['skip'])
    else:
        skip = 0
    if 'ss' in request.form:
        ss = request.form['ss']
    else:
        ss = ""
    if request.form['_id'] == None:
        return "form problem"
    else:
        note_id = request.form['_id']
        doc = notes.find_one({"_id": ObjectId(note_id)})
        if doc == None:
            return "form problem"
        else:
            date = doc['date'] + datetime.timedelta(minutes=-tzoffset) 
            datestr = date.strftime("%a %d %b %Y %H:%M:%S")
    msg = ""
    if delete_note:
        notes.delete_one({"_id": ObjectId(note_id)})
        msg = "Note deleted"
    else:
        if len(title) or len(body):
            notes.update_one({"_id": ObjectId(note_id)}, {"$set": {"title": title, "body": body}})
            msg = "Note updated"
    return get_notes(ss, tzoffset, skip, "edit", msg)


@app.route("/add", methods=["GET", "POST"])
def notes_add():
    user = request.cookies.get('user')
    if not cookie_good(user):
        return(make_response("not allowed"))
    if request.method == 'GET':
        colori = random.randint(0, len(colors)-1)
        resp =  render_template('add.html', ncolor=colors[colori])
        return resp
    elif request.method == 'POST':
        #print(request.form)
        title = ""
        body = ""
        tzoffset = 0
        if (request.form['notebody'] != None and len(request.form['notebody']) > 5000):
            return "form problem"
        else:
            body = request.form['notebody']
        if (request.form['notetitle'] != None and len(request.form['notetitle']) > 500):
            return "form problem"
        else:
            title = request.form['notetitle']
        if 'tzoffset' in request.form:
            tzoffset = int(request.form['tzoffset'])
        msg = "Note had no content"
        if len(title) or len(body):
            notes = mongo.db.notes
            ret = notes.insert_one({'title' : title, 'body' : body, 'date' : datetime.datetime.now()})
            print("inserted id: " + str(ret.inserted_id))
            msg="Note added"

        skip = 0
        ss = ""
        form = "add"
        return get_notes(ss, tzoffset, skip, form, msg)


# Use a random string as a URL which allows you to set a cookie
# This one was gotten by running the following at the terminal:
# echo "import uuid; print(uuid.uuid4())" | python - 
# NOTE: Dont ever make this url public!
@app.route("/9dd33c0d-4c6c-4b62-ab92-e0698c4f9a25", methods=["GET"])
def notes_set_cookie():
    if request.method == 'GET':
        cc = mongo.db.cookie #cookie collection
        results = cc.find({})
        cookie = ""
        for doc in results:
            cookie = doc['user']
        if cookie == "":
            cookie = str(uuid.uuid4())
            ret = cc.insert_one({'user' : cookie})
        colori = random.randint(0, len(colors)-1)
        resp =  make_response(render_template('view.html', ncolor=colors[colori], message="Cookie set"))
        resp.set_cookie("user", value=cookie, path="/", max_age=32140800)
        return resp


def cookie_good(cookie):
    cc = mongo.db.cookie #cookie collection
    results = cc.find({})
    for doc in results:
        if cookie == doc['user']:
            return True
    return False


def get_notes(ss, tzoffset, skip, form="", msg=""):
    notes = mongo.db.notes
    oldest_first = False
    limit=3
    if ss == "$#@":
        oldest_first = True
        findparm = {}
    elif ss.startswith("$#"):
        try:
            daysago = int(ss[2:])
        except:
            daysago = 0
        #print("days ago = " + str(daysago))
        #first you want to get into the user's timezone to get the current day there
        searchdate = datetime.datetime.now() + datetime.timedelta(minutes=-tzoffset)
        #then you want to get to the start of the day they want
        searchdate = searchdate + datetime.timedelta(days=-daysago)
        #and get to 12AM...
        hour = searchdate.hour
        minute = searchdate.minute
        second = searchdate.second
        microsecond = searchdate.microsecond
        searchdate = searchdate + datetime.timedelta(hours=-hour)
        searchdate = searchdate + datetime.timedelta(minutes=-minute)
        searchdate = searchdate + datetime.timedelta(seconds=-second)
        searchdate = searchdate + datetime.timedelta(microseconds=-microsecond)
        #then you want to get back to UTC again since the db contains dates in UTC
        # print("searchdate = " + str(searchdate))
        # e.g. for US east coast 12 AM midnight would be 04:00:00 AM

        findparm = {'date' : {"$gte" : searchdate}}
        oldest_first = True
    else:
        regx = re.compile(ss, re.IGNORECASE)
        findparm = {'$or':[{'title' : regx}, {'body': regx}]}
    #print("findparm: " + str(findparm)) 
    notelist = []
    counter = 0
    if oldest_first:
        results = notes.find(findparm, skip=skip, limit=limit)
    else:    
        results = notes.find(findparm, skip=skip, limit=limit).sort("_id",-1)
    # only for the search after edit do we want to retry once if the search did not find any results
    # since the note could have been deleted and was the last one for that skip count, then
    # we retry once more with the previous skip
    if form == "edit":
        find_count = 2 
    else:
        find_count = 1 
    while find_count > 0:
        counter = 0
        find_count -= 1
        for doc in results:
            find_count = 0
            counter += 1
            if counter == limit:
                break
            date = doc['date'] + datetime.timedelta(minutes=-tzoffset)
            datestr = date.strftime("%a %d %b %Y %H:%M:%S")
            # create hyperlinks for those appearing in the text
            ebody = enhance_text(ss, doc['body'])
            etitle = enhance_text(ss, doc['title'])
            if doc['title'].lower().startswith("http://") or doc['title'].lower().startswith("https://"):
                notelist.append({'_id':str(doc['_id']), 'link':etitle, 'body':ebody, 'date':datestr}) 
            else:    
                notelist.append({'_id':str(doc['_id']), 'title':etitle, 'body':ebody, 'date':datestr}) 

        if counter == 0 and skip >= 2 and find_count > 0:
            skip -= 2
            if oldest_first:
                results = notes.find(findparm, skip=skip, limit=limit)
            else:    
                results = notes.find(findparm, skip=skip, limit=limit).sort("_id",-1)
        else:
            find_count = 0
    if counter == limit:
        next_skip = skip + counter - 1
    else:
        next_skip = -1 # means no next
    if skip - (limit-1) >= 0:
        prev_skip = skip - (limit-1)
    else:
        prev_skip = -1 # means no prev
    colori = random.randint(0, len(colors)-1)
    return render_template('view.html', ncolor=colors[colori], notes=notelist, 
            searchterm=ss, next_skip=next_skip, prev_skip=prev_skip, current_skip=skip, message=msg)


@app.route("/", methods=["GET", "POST"])
def notes_view():
    user = request.cookies.get('user')
    if not cookie_good(user):
        resp = make_response("not allowed")
        return(resp)

    if request.method == 'GET':
        colori = random.randint(0, len(colors)-1)
        resp =  render_template('view.html', ncolor=colors[colori])
        return resp
    elif request.method == 'POST':
        #print(request.form)
        isgood = True
        if 'search_box' in request.form:
            print("search_box=" + request.form['search_box'])
            ss = request.form['search_box']
        else:
            isgood = False
        if 'skip' in request.form:
            print("skip=" + request.form['skip'])
            skip = request.form['skip']
            if skip.isnumeric():
                skip = int(skip)
            else:
                skip = 0 # default start from beginning
        else:
            skip = 0 # default start from the beginning
        if 'tzoffset' in request.form:
            tzoffset = int(request.form['tzoffset'])
        else:
            tzoffset = 0
        if not isgood:
            response = make_response(redirect('/notes'))
            return response
        return get_notes(ss, tzoffset, skip)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
    print("after app.run.....")
